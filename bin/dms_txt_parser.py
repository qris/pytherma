import argparse
import re

from collections import namedtuple

from pytherma import decoding

# example: "000079: 2020-06-02 20:37:15.6557978 +0.0000043"
header_regex = re.compile(r'^(\d{6}): \d{4}-\d{2}-\d{2} (\d{2}:\d{2}:\d{2}\.\d+)')

# example: " 53 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00   S..............."
data_regex = re.compile(r'^(( [0-9A-F]{2}){1,16})   ')

Packet = namedtuple('Packet', 'number is_read timestamp data_bytes')

def read_packet(handle, is_read):
    header_line = handle.readline()
    if header_line == '' or header_line == '\x00':
        return None

    match = header_regex.match(header_line)
    assert match is not None, f"{header_line!r} at {handle}:{handle.tell():x}"
    packet_no = int(match.group(1))
    packet_ts = match.group(2)

    blank_line = handle.readline()
    assert blank_line == '\n', repr(blank_line)

    data_bytes = []

    while True:
        # Record position before reading another line, so we can rewind when we read another header line
        previous_position = handle.tell()
        data_line = handle.readline()
        if data_line == '\n':
            continue

        if data_line == '' or data_line == '\x00':
            break

        if header_regex.match(data_line):
            handle.seek(previous_position)
            break

        match = data_regex.match(data_line)
        assert match is not None, (repr(data_line), handle.tell())

        hex_byte_strs = match.group(1)[1:].split(' ')
        data_bytes.extend([int(hex_byte_str, 16) for hex_byte_str in hex_byte_strs])

    return Packet(packet_no, is_read, packet_ts, data_bytes)

def main():
    parser = argparse.ArgumentParser(description='Parse Data View exported from HHD Device Monitoring Studio')
    parser.add_argument('write_file', help='Text file containing bytes WRITTEN to device (out)')
    parser.add_argument('read_file', help='Text file containing bytes READ from device (in)')
    parser.add_argument('--changes', action='store_true',
                        help="Show only lines where the response to a command differs from the previous one")
    parser.add_argument('--decode', action='store_true',
                        help="Decode changes as Daikin Altherma variables where known")
    args = parser.parse_args()

    packets = []

    with open(args.write_file, encoding='iso8859-1') as written:
        while True:
            result = read_packet(written, is_read=False)
            if result is None:
                break
            packets.append(result)

    with open(args.read_file, encoding='iso8859-1') as read:
        while True:
            result = read_packet(read, is_read=True)
            if result is None:
                break
            packets.append(result)

    #for packet in sorted(packets):
    #    packet_no, response, data_bytes = packet
    #    print('   ' if response else '>>>', packet_no, data_bytes)

    packets.sort()

    command_to_most_recent_response = {}

    while len(packets) > 0:
        command = packets.pop(0)
        response = packets.pop(0)
        assert command.is_read == False, (command, response)
        assert response.is_read == True, (command, response)
        diffs = ''
        decoded = []

        if args.changes:
            command_bytes = bytes(command.data_bytes)
            last_response = command_to_most_recent_response.get(command_bytes)
            if last_response is not None and last_response.data_bytes == response.data_bytes:
                continue
            command_to_most_recent_response[command_bytes] = response

            if last_response is not None:
                diffs = []
                # assert len(response.data_bytes) == len(last_response.data_bytes), (command, last_response, response)
                for i in range(max(len(last_response.data_bytes), len(response.data_bytes))):
                    old_byte = last_response.data_bytes[i] if i < len(last_response.data_bytes) else None
                    new_byte = response.data_bytes[i] if i < len(response.data_bytes) else None
                    if new_byte != old_byte:
                        diffs.append((i, old_byte, new_byte))

            if args.decode:
                values = decoding.decode(command.data_bytes, response.data_bytes)
                for i, (decoder, new_value) in values.items():
                    old_value = (decoder.decode(command.data_bytes, last_response.data_bytes)
                                 if last_response is not None else None)
                    decoded.append(f"# {decoder.number}: {decoder.label}: {old_value} => {new_value}")

        if diffs:
            print("")

        for item in decoded:
            print(item)

        print(f"# {command.number},{response.number} {command.timestamp} {diffs}\n"
              f"[{command.data_bytes}, {response.data_bytes}]")

if __name__ == '__main__':
    main()
