""" Simulates a Daikin Altherma's responses to serial commands. Used by tests. """

import argparse
import datetime
import random
import serial
import sys

from more_itertools import bucket, one

import pytherma.comms

simulated_command_responses = [
    [bytes(command), bytes(response)]
    for command, response in [
        # [[36, 36, 36], [21, 234, 21, 234]],
        # [[2, 78, 175, 48, 48, 48, 48, 189, 3], [254]],
        [[2, 78, 175], []],
        [[2, 83, 170], [83, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 172]],
        [[2, 80, 173], [21, 234]],
        [[2, 84, 169], [84, 180, 26, 84, 27, 104, 33, 156, 26, 24, 53, 1, 26, 0, 0, 0, 0, 199]],
        [[2, 85, 168], [85, 1, 0, 0, 0, 0, 132, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 34]],
        [[2, 84, 169], [84, 204, 26, 84, 27, 104, 33, 156, 26, 24, 53, 1, 26, 0, 0, 0, 0, 175]],
        [[36, 36, 36], [21, 234]],
        [[3, 64, 160, 28], [21, 234]],
        [[3, 64, 161, 27], [21, 234]],
        [[3, 64, 0, 188], [64, 0, 15, 4, 1, 0, 1, 1, 1, 0, 2, 1, 1, 4, 57, 60, 43]],
        [[3, 64, 16, 172], [64, 16, 18, 0, 0, 0, 0, 0, 0, 72, 3, 0, 0, 0, 0, 0, 0, 0, 0, 82]],
        [[3, 64, 17, 171], [64, 17, 8, 2, 49, 149, 1, 2, 5, 214]],
        [[3, 64, 32, 156], [64, 32, 19, 205, 0, 0, 0, 24, 1, 0, 0, 190, 0, 0, 0, 255, 0, 131, 0, 1, 101]],
        [[3, 64, 33, 155], [64, 33, 18, 5, 0, 0, 0, 19, 0, 0, 190, 0, 0, 0, 0, 0, 0, 0, 0, 182]],
        [[3, 64, 48, 140], [64, 48, 13, 0, 0, 0, 194, 1, 0, 0, 0, 0, 0, 0, 191]],
        [[3, 64, 96, 92], [64, 96, 19, 128, 0, 64, 0, 0, 0, 71, 38, 2, 250, 0, 160, 0, 27, 242, 118, 0, 0]],
        [[3, 64, 97, 91], [64, 97, 18, 128, 0, 78, 1, 10, 1, 11, 1, 17, 1, 18, 2, 4, 1, 0, 0, 59]],
        [[3, 64, 98, 90], [64, 98, 19, 128, 0, 128, 94, 1, 210, 0, 0, 1, 253, 255, 0, 100, 0, 0, 0, 0, 184]],
        [[3, 64, 99, 89], [64, 99, 10, 128, 0, 1, 112, 100, 50, 21, 1, 181]],
        [[3, 64, 100, 88], [64, 100, 14, 128, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 203]],
        [[3, 64, 97, 91], [64, 97, 18, 128, 0, 79, 1, 10, 1, 11, 1, 17, 1, 18, 2, 4, 1, 0, 0, 58]],

    ]
]

three_dollars = b'$$$'


# Some commands have multiple responses, in which case we might receive any one of them.
command_to_responses = (
    bucket(simulated_command_responses, key=lambda command_and_response: command_and_response[0])
)

command_to_responses = {
    k: [list(response[1]) for response in command_to_responses[k]]
    for k in command_to_responses
}


class DaikinSimulator:
    """ Simulates a Daikin Altherma's responses to serial commands. Used by tests. """

    response_buffer = b''

    def write(self, command):
        """ Write a simulated command.

        This places an appropriate response into the response buffer, which must be empty (the
        last response must have been completely read). The read() method then returns the bytes
        of the response.
        """
        assert self.response_buffer == b'', (
            f"Data left in response buffer: {self.response_buffer}"
        )
        responses = [
            canned_response
            for canned_command, canned_response in simulated_command_responses
            if canned_command == command
        ]
        assert len(responses) > 0, f"Unknown command: {command}"
        response = random.choice(responses)
        self.response_buffer = response

    def can_read(self):
        """ Return whether (or not) there is data in the response buffer, waiting to be read.

        If all requests returned a response, then this would not be needed, as we could always
        read one byte to determine the format of the rest. Unfortunately, some commands return
        no response!
        """
        return len(self.response_buffer) > 0

    def read(self, length=1):
        """ Read some bytes from the start of the response buffer, and removes them.

        You may not try to read more bytes than are in the buffer. This forces you to read the
        correct number of bytes to determine the length of the response, and then read it
        exactly. Reading too much would block forever in the real world.
        """
        assert length <= len(self.response_buffer), (
            f"Read too large: {length} bytes requested, {len(self.response_buffer)} available"
        )
        result = self.response_buffer[:length]
        remain = self.response_buffer[length:]
        self.response_buffer = remain
        return result


class Logger:
    """ Logs requests and responses. Can be passed to a Framer. """

    def log_command(self, command):
        """ Log a command (request) packet. """
        if sys.version_info >= (3, 8):
            print(f"{datetime.datetime.now().time()} > {command.hex(' ')}")
        else:
            hex_str = ' '.join(bytes(b).hex() for b in command)
            print(f"{datetime.datetime.now().time()} > {hex_str}")

    def log_response(self, response):
        """ Log a response (data) packet. """
        if sys.version_info >= (3, 8):
            print(f"{datetime.datetime.now().time()} < {response.hex(' ')}")
        else:
            hex_str = ' '.join(bytes(b).hex() for b in response)
            print(f"{datetime.datetime.now().time()} < {hex_str}")


def read_complete_response(device_read):
    """ Read the exact number of bytes required (by calling device_read(size)).

    Returns the bytes read.
    """
    # We need to read the exact number of bytes from the device, so we need to determine
    # how many that is.
    buffer = device_read(1)

    if len(buffer) == 0:
        return buffer

    if buffer[0] == three_dollars[0]:
        buffer += device_read(2)
    elif buffer[0] in (83, 84, 85):
        buffer += device_read(17)
    elif buffer[0] == 21:
        buffer += device_read(1)
        assert buffer[1] == 234
    elif buffer[0] == 64:
        buffer += device_read(2)
        remaining_length = buffer[-1] - 1
        buffer += device_read(remaining_length)
    else:
        raise ValueError(f"Unrecognised response in buffer: {buffer}")

    return buffer


class Framer:
    """ Collects received bytes into request frames, and dispatches to a simulated device.

    Used by bin/dchecker_spoofer.py to handle incoming raw serial data persuade DChecker to talk to it over a serial null modem
    connection, by returning correctly-formatted responses to its requests.
    """

    def __init__(self, device, logger=None):
        self.device = device
        self.logger = logger
        self.request_buffer = b''
        self.response_buffer = b''

    def _remove_length(self, length):
        removed = self.request_buffer[:length]
        self.request_buffer = self.request_buffer[length:]
        return removed

    def write(self, data_bytes):
        """ Buffer some data. When a complete command is buffered, send it to our device.

        Unlike DaikinSimulator.write(), this can be called with any amount of received data.
        The caller doesn't need to understand the Daikin framing, because this class deals
        with it. The caller just reads some serial data and feeds it to us, using this method,
        and then calls read() to fetch any data from our device (presumably to send it back
        to D-Checker).

        Returns the number of bytes remaining to complete the current command, if known, or
        the number of bytes to determine the command length, or None otherwise. This helps
        the caller to read multiple bytes from the serial port, for efficiency.
        """
        assert not self.device.can_read(), self.device.response_buffer
        assert len(data_bytes) > 0, "Framer does not accept empty writes"

        self.request_buffer += data_bytes

        if self.request_buffer.startswith(three_dollars[:1]):
            request_len = len(three_dollars)
        elif self.request_buffer[:1] == bytes([2]):
            # Always length 3?
            request_len = 3
        elif self.request_buffer[:1] == bytes([3]):
            # Always length 4?
            request_len = 4
        else:
            raise ValueError(f"Unrecognised request in buffer: {self.request_buffer}")

        if len(self.request_buffer) < request_len:
            # More bytes will hopefully be added soon, and then we'll send the request.
            return request_len - len(self.request_buffer)

        request = self._remove_length(request_len)

        if self.logger is not None:
            self.logger.log_command(request)

        self.device.write(request)

        # Since we just wrote a command to the device, it's likely that there will be a response
        # waiting to be read back (but not guaranteed, because not every request has a response).
        if not self.device.can_read():
            return 0  # We have read a complete command, so we don't need more bytes just now

        # We need to read the exact number of bytes from the DaikinSimulator, so we need to
        # determine how many that is.
        try:
            self.response_buffer = read_complete_response(self.device.read)
        except AssertionError as exc:
            raise AssertionError(f"Failed to read expected response to {list(request)}: {exc}")

        if self.logger is not None:
            self.logger.log_response(self.response_buffer)

        if self.response_buffer[0] == three_dollars[0]:
            assert self.response_buffer == three_dollars
        else:
            expected_checksum = one(pytherma.comms.calculate_checksum(self.response_buffer[:-1]))
            assert self.response_buffer[-1] == expected_checksum, (
                f"Expected checksum {expected_checksum} but found {self.response_buffer[-1]} "
                f"in {list(self.response_buffer)} for {list(request)}"
            )

        return 0  # We have read a complete command, so we don't need more bytes just now

    def read(self):
        """ Return the complete response to the last command, if any.

        The caller should always call this after writing some bytes to us, since it won't
        block or raise exceptions. Therefore no can_read() method is needed.
        """
        if self.device.can_read():
            late_response = read_complete_response(self.device.read)
            if self.logger is not None:
                self.logger.log_response(late_response)
            self.response_buffer += late_response

        response = self.response_buffer
        self.response_buffer = b''
        return response


class SerialWrapper:
    """ Implements the Serial interface on an underlying Framer device.

    You can wrap this around a Framer device and pass it to Passthrough, which will then
    communicate with the wrapper Framer (presumably wrapped around a DaikinSimulator).

    This is used to test the Passthrough without a real Serial port.
    """

    def __init__(self, framer):
        self.framer = framer
        self.response_buffer = b''

    def write(self, buffer):
        """ Write the bytes in the supplied buffer to the Framer.

        Any number of bytes may be written. The Framer will properly frame them and pass
        them to the DaikinSimulator underneath.
        """
        self.framer.write(buffer)

    def read(self, size=1):
        """ Read and return up to size bytes. """
        if len(self.response_buffer) == 0:
            self.response_buffer = self.framer.read()
        size = min(size, len(self.response_buffer))
        result = self.response_buffer[:size]
        self.response_buffer = self.response_buffer[size:]
        return result


class Passthrough:
    """ Implements the Framer interface on an underlying Serial device.

    You can wrap this around a Serial device and pass it to device_simulator_loop,
    which will communicate with the real Daikin device attached to the Serial port.
    This can be used to insert a simulator between two real COM ports (or a virtual
    and a real COM port), which allows us to log the command and response packets.

    Alternatively you can pass it a SerialWrapper wrapped around a Framer, to test
    the Passthrough itself.
    """

    def __init__(self, serial_port):
        self.serial_port = serial_port
        serial_port.timeout = 0  # non-blocking read()

    def write(self, data_bytes):
        """ Process some data read from another Serial port by the device_simulator_loop.

        We will write it to our own Serial port (or SerialWrapper).
        """
        self.serial_port.write(data_bytes)

    def read(self):
        """ Return whatever is available to read from the Serial port right now.

        The caller should always call this after writing some bytes to us, since it won't
        block or raise exceptions. Therefore no can_read() method is needed.
        """
        return read_complete_response(self.serial_port.read)


def device_simulator_loop(device, dchecker_serial_port):
    """ Read serial commands (presumably from D-Checker) and respond to them.

    The responses are determined by the supplied underlying device. They might be canned
    responses, or probes for D-Checker itself.
    """
    framer = Framer(device, Logger())
    buffer = bytearray(10)

    while True:
        length = dchecker_serial_port.readinto(buffer)
        framer.write(buffer[:length])
        dchecker_serial_port.write(framer.read())


def device_simulator(cmdline_args=None):
    """ Run the device simulator as a command-line application. """
    parser = argparse.ArgumentParser(description=("Pretend to be a Daikin Altherma ASHP and "
                                                  "respond to serial commands from D-Checker."))
    parser.add_argument('port', help="Name of the serial port device to open, e.g. COM3 or "
                        "/dev/ttyUSB0", metavar="device_name")
    parser.add_argument('--passthrough', help="Forward requests to another serial port "
                        "(a real Daikin device) instead of the simulator, e.g. COM3 or "
                        "/dev/ttyUSB0", metavar="device_name")

    args = parser.parse_args(cmdline_args)

    if args.passthrough:
        device = Passthrough(serial.Serial(args.passthrough, 9600))
    else:
        device = DaikinSimulator()

    dchecker_serial_port = serial.Serial(args.port, 9600)
    device_simulator_loop(device, dchecker_serial_port)
