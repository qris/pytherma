""" Tests for the DaikinSimulator and companion classes. """

import more_itertools
import random
import unittest

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
            framer.write(command)
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
        command_to_responses = (
            more_itertools.bucket(pytherma.simulator.simulated_command_responses,
                                  key=lambda command_and_response: command_and_response[0])
        )
        command_to_responses = {
            k: [list(response[1]) for response in command_to_responses[k]]
            for k in command_to_responses
        }
        commands = list(command_to_responses)

        current_index = 0
        current_pos = 0
        write_buf = b''
        random.seed(1)

        while current_index < len(commands):
            current_command = commands[current_index]
            expected_responses = command_to_responses[current_command]

            write_len = random.randint(1, 4)
            write_buf += current_command[current_pos:current_pos + write_len]
            current_pos += write_len

            self.assertTrue(len(write_buf) > 0, f"{current_index} {current_pos}")

            # Framer should accept any amount of data (>= 1 byte) as that's the point of it:
            framer.write(write_buf)
            write_buf = b''

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
