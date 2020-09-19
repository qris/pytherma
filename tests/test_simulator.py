""" Tests for the DaikinSimulator and companion classes. """

import more_itertools
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
