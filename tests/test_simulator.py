""" Tests for the DaikinSimulator and companion classes. """

import more_itertools
import random
import serial
import unittest

from unittest.mock import MagicMock, patch

import pytherma.simulator


class SimulatorTest(unittest.TestCase):
    """ Tests that DaikinSimulator and Framer respond properly. """

    def test_complete_requests(self):
        """ Tests that the DaikinSimulator and Framer respond properly to complete requests.

        This is the easy case: receiving the entire request in one go.
        """
        framer = pytherma.simulator.Framer(pytherma.simulator.DaikinSimulator())

        # Some commands have multiple responses, in which case we might receive any one of them.
        command_to_responses = (
            more_itertools.bucket(pytherma.simulator.simulated_command_responses,
                                  key=lambda command_and_response: command_and_response[0])
        )

        for command in command_to_responses:
            expected_responses = [
                command_and_response[1] for command_and_response in command_to_responses[command]
            ]

            self.assertEqual(0, framer.write(command), "Framer.write() should return the "
                             "number of bytes left to complete this command, which should be 0")

            actual_response = framer.read()
            self.assertIn(actual_response, expected_responses,
                          f"Unexpected response to {list(command)}")

    def test_partial_writes(self):
        """ Tests that the Framer can correctly assemble request frames from scattered writes.

        This is necessary because serial port communication is byte-oriented and has no concept
        of framing, but the DaikinSimulator requires correct framing, so we need the Framer to
        frame the incoming bytes into packets.
        """
        framer = pytherma.simulator.Framer(pytherma.simulator.DaikinSimulator())

        # Some commands have multiple responses, in which case we might receive any one of them.
        command_to_responses = pytherma.simulator.command_to_responses
        commands = list(command_to_responses)

        current_index = 0
        current_pos = 0
        write_buf = b''
        random.seed(1)

        while current_index < len(commands):
            current_command = commands[current_index]
            expected_responses = command_to_responses[current_command]

            write_len = random.randint(1, 4)
            add_to_buf = current_command[current_pos:current_pos + write_len]
            write_buf += add_to_buf
            current_pos += len(add_to_buf)

            self.assertTrue(len(write_buf) > 0, f"{current_index} {current_pos}")

            # Framer should accept any amount of data (>= 1 byte) as that's the point of it:
            actual_write_result = framer.write(write_buf)
            write_buf = b''

            if current_command[:1] == b'$':
                command_len_if_known = 3
            elif current_command[:1] == bytes([2]):
                command_len_if_known = 3
            elif current_command[:1] == bytes([3]):
                command_len_if_known = 4
            else:
                self.fail("Unknown command type {list(current_command)}, don't know how "
                          "Framer will determine its length")

            expected_write_result = command_len_if_known - current_pos
            self.assertEqual(expected_write_result, actual_write_result,
                             "Framer.write() should have returned the number of bytes left "
                             "to complete this command, or to determine its length")

            if current_pos >= len(current_command):
                actual_response = framer.read()

                if [] not in expected_responses:
                    self.assertTrue(len(actual_response) > 0,
                                    f"Unexpectedly no response to command "
                                    f"{list(current_command)} at position {current_index} "
                                    f"which should always have a response")

                self.assertIn(list(actual_response), expected_responses)

            unexpected_response = framer.read()
            self.assertEqual(b'', unexpected_response,
                             f"Unexpectedly found data to read in buffer after incomplete "
                             f"command {list(current_command)} at position {current_pos}")

            # If we have finished the current command, then start on the next one:
            if current_pos >= len(current_command):
                # Reset ready to send (part of) the next command too:
                current_index += 1
                current_pos = 0

    def test_device_simulator(self):
        """ Test that the device_simulator() main loop works as expected. """
        buffer = b''.join(pytherma.simulator.command_to_responses)  # All keys, concatenated
        buffer_pos = [0]

        def mock_readinfo(read_buffer):
            if buffer_pos[0] == len(buffer):
                raise KeyboardInterrupt("force exit from main loop")

            read_len = random.randint(1, 4)
            if read_len > len(buffer) - buffer_pos[0]:
                read_len = len(buffer) - buffer_pos[0]

            read_buffer[:read_len] = buffer[buffer_pos[0]:buffer_pos[0] + read_len]
            buffer_pos[0] += read_len
            return read_len

        mock_serial = MagicMock(spec=serial.Serial)
        mock_serial().readinto = mock_readinfo
        with patch('serial.Serial', new=mock_serial):
            with self.assertRaises(KeyboardInterrupt):
                pytherma.simulator.device_simulator(['/dev/ttyUSB0'])
