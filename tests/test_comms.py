""" Tests for the comms module. """

import unittest

from pytherma import comms, simulator


class PacketFunctionsTest(unittest.TestCase):
    """ Tests for the comms module. """

    def test_checksums(self):
        """ Test that calculate_checksum() works as expected. """
        for i, (command, response) in enumerate(simulator.autodetect_command_responses):
            if command == b'$$$':
                continue

            self.assertEqual(command[-1:], comms.calculate_checksum(command[:-1]),
                             (i, command, response))
            if len(response) > 0:
                self.assertEqual(response[-1:], comms.calculate_checksum(response[:-1]),
                                 (i, command, response))

        self.assertEqual(bytes([234]), comms.calculate_checksum(bytes([21])))

    def test_execute_command(self):
        """ Test that execute_command() sends commands and receives the expected responses. """
        sim = simulator.DaikinSimulator()
        self.assertEqual(bytes([21, 234]), comms.execute_command(sim, bytes([3, 64, 160, 28])))
        self.assertEqual(bytes([21, 234]), comms.execute_command(sim, b'$$$'))
