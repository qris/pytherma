""" Simulates a Daikin Altherma's responses to serial commands. Used by tests. """

import datetime
import random

from more_itertools import one

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
    """ An adaptor/wrapper around a DaikinSimulator which logs requests and responses.

    Can be wrapped around a DaikinSimulator and passed to a Framer like this:

        Framer(Logger(DaikinSimulator()))
    """

    def __init__(self, device):
        self.device = device

    def write(self, command):
        """ Write a command (request) to the wrapped Device. """
        print(f"{datetime.datetime.now().time()} > {command.hex(' ')}")
        self.device.write(command)

    def can_read(self):
        """ Return whether (or not) there is data in the response buffer, waiting to be read. """
        return self.device.can_read()

    def read(self, length=1):
        """ Read some response bytes from the wrapped Device. """
        response = self.device.read(length)
        print(f"{datetime.datetime.now().time()} < {response.hex(' ')}")
        return response


class Framer:
    """ Collects received bytes into request frames, and dispatches to a simulated device.

    Used by bin/dchecker_spoofer.py to handle incoming raw serial data persuade DChecker to talk to it over a serial null modem
    connection, by returning correctly-formatted responses to its requests.
    """

    three_dollars = bytes([36, 36, 36])
    error_response = bytes([21, 234])

    def __init__(self, device):
        self.device = device
        self.request_buffer = b''
        self.response_buffer = b''

    def _remove_length(self, length):
        removed = self.request_buffer[:length]
        self.request_buffer = self.request_buffer[length:]
        return removed

    def _remove_if_prefix(self, prefix):
        if self.request_buffer[:len(prefix)] == prefix:
            return self._remove_length(len(prefix))
        else:
            return b''

    def _read_and_buffer_length(self, length):
        result = self.device.read(length)
        self.response_buffer += result
        return result

    def write(self, data_bytes):
        """ Ingest some data received over serial comms.

        Unlike the Simulator, this can be called with any amount of received data. The caller
        doesn't need to understand the Daikin framing, because this class deals with it.
        The caller just reads some serial data and feeds it to us, using this method, and then
        calls read() to fetch any data that we have decided to send back to D-Checker.
        """
        assert not self.device.can_read(), self.device.response_buffer
        assert len(self.response_buffer) == 0, self.response_buffer
        assert len(data_bytes) > 0, "Framer does not accept empty writes"

        self.request_buffer += data_bytes

        if self.request_buffer.startswith(self.three_dollars[:1]):
            request_len = len(self.three_dollars)
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
            return

        request = self._remove_length(request_len)
        self.device.write(request)

        # Since we just wrote a command to the device, it's likely that there will be a response
        # waiting to be read back (but not guaranteed, because not every request has a response).
        if not self.device.can_read():
            return

        try:
            first_byte = self._read_and_buffer_length(1)
            if first_byte == self.three_dollars[0]:
                self._read_and_buffer_length(2)
                assert self.response_buffer == self.three_dollars
            elif one(first_byte) in (83, 84, 85):
                self._read_and_buffer_length(17)
            elif one(first_byte) == 21:
                assert self._read_and_buffer_length(1) == bytes([234])
            elif one(first_byte) == 64:
                self._read_and_buffer_length(2)
                remaining_length = self.response_buffer[-1] - 1
                self._read_and_buffer_length(remaining_length)
            else:
                raise ValueError(f"Unrecognised response in buffer: "
                                 f"{first_byte + self.device.response_buffer}")
        except AssertionError as exc:
            raise AssertionError(f"Failed to read expected response to {list(request)}: {exc}")

        if self.response_buffer != self.three_dollars:
            expected_checksum = one(pytherma.comms.calculate_checksum(self.response_buffer[:-1]))
            assert self.response_buffer[-1] == expected_checksum, (
                f"Expected checksum {expected_checksum} but found {self.response_buffer[-1]} "
                f"in {list(self.response_buffer)} for {list(request)}"
            )

    def read(self):
        """ Return whatever is in the response buffer, waiting to be read.

        The caller should always call this after writing some bytes to us, since it won't
        block or raise exceptions. Therefore no can_read() method is needed.
        """
        response = self.response_buffer
        self.response_buffer = b''
        return response
