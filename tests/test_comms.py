import unittest

from pytherma import comms, simulator

class PacketFunctionsTest(unittest.TestCase):
    def test_checksums(self):
        for i, (command, response) in enumerate(simulator.autodetect_command_responses):
            if command == b'$$$':
                continue

            self.assertEqual(command[-1:], comms.calculate_checksum(command[:-1]), (i, command, response))
            if len(response) > 0:
                self.assertEqual(response[-1:], comms.calculate_checksum(response[:-1]), (i, command, response))

        self.assertEqual(bytes([234]), comms.calculate_checksum(bytes([21])))

    def test_execute_command(self):
        sim = simulator.DaikinSimulator()
        self.assertEqual(bytes([21, 234]), comms.execute_command(sim, bytes([3, 64, 160, 28])))
        self.assertEqual(bytes([21, 234]), comms.execute_command(sim, b'$$$'))

