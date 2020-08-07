""" Simulates a Daikin Altherma's responses to serial commands. Used by tests. """

import random

autodetect_command_responses = [
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
            for canned_command, canned_response in autodetect_command_responses
            if canned_command == command
        ]
        assert len(responses) > 0, f"Unknown command: {command}"
        response = random.choice(responses)
        self.response_buffer = response

    def read(self, length=1):
        """ Read some bytes from the start of the response buffer, and removes them.

        You may not try to read more bytes than are in the buffer. This forces you to read the
        correct number of bytes to determine the length of the response, and then read it
        exactly. Reading too much would block forever in the real world.
        """
        assert length <= len(self.response_buffer), (
            f"Read too large: {len(self.response_buffer)} bytes available"
        )
        result = self.response_buffer[:length]
        remain = self.response_buffer[length:]
        self.response_buffer = remain
        return result
