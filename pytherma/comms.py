def calculate_checksum(packet_bytes):
    result = sum(packet_bytes) % 256
    return bytes([255 - result])


def execute_command(device, command):
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


