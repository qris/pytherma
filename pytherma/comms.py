""" Functions that communicate with a Daikin Altherma by sending and receiving serial commands. """


def calculate_checksum(packet_bytes):
    """ Calculate the checksum byte for a packet.

    This should be passed the packet data (bytes), up to but not including the final byte, which
    contains the checksum. So the return from this function should be appended to the packet
    before sending.
    """
    result = sum(packet_bytes) % 256
    return bytes([255 - result])


def execute_command(device, command):
    """ Write a command to a device (e.g. a DaikinSimulator) and read the response. """
    device.write(command)
    response = bytearray(device.read(2))

    if response[0] == 21:
        pass
    elif response[0] >= 83 and response[0] <= 85:
        response += device.read(15)
    elif response[0] == 64:
        response += device.read(1)
        response_length = response[-1]
        response += device.read(response_length - 1)
    else:
        raise AssertionError(f"response type not understood, unable to determine length: {response[0]}")

    expected_checksum = calculate_checksum(response[:-1])
    assert response[-1:] == expected_checksum, f"Wrong checksum: expected {expected_checksum} but found {response[-1:]} in {response}"
    return bytes(response)
