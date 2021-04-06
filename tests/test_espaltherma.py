""" Tests for the functions in the espaltherma module.

Those functions convert ESPAltherma definition files to our CommandDecoder structures.
"""

import unittest

from pytherma import decoding, espaltherma
from pytherma.decoding import CommandDecoder
from pytherma.espaltherma import parse_espaltherma_definition


class ESPAlthermaTest(unittest.TestCase):
    """ Tests for the functions in the espaltherma module. """

    def test_parse_espaltherma_definition(self):
        """ Tests that parse_espaltherma_definition works as expected. """
        # Extract from https://github.com/raomin/ESPAltherma/blob/main/include/converters.h
        result = parse_espaltherma_definition(
            '//{0x00,11,152,1,-1,"O/U MPU ID (yy)"},\n'
            '//{0x00,12,105,1,-1,"O/U capacity (kW)"},\n'
            '//{0x10,0,217,1,-1,"Operation Mode"},\n'
            '//{0x10,1,307,1,-1,"Thermostat ON/OFF"},',
            output_text=True
        )

        self.assertEqual(
            {
                (3, 64, 0): [
                    "CommandDecoder(14, decode_byte_1, '00.11.152', 'O/U MPU ID (yy)')",
                    "CommandDecoder(15, decode_byte_10, '00.12.105', 'O/U capacity (kW)')",
                ],
                (3, 64, 16): [
                    "CommandDecoder(3, decode_operation_mode, '10.0.217', 'Operation Mode')",
                    "CommandDecoder(4, decode_bits[7], '10.1.307', 'Thermostat ON/OFF')",
                ],
            }, result
        )

        result = parse_espaltherma_definition(
            '//{0x00,11,152,1,-1,"O/U MPU ID (yy)"},\n'
            '//{0x00,12,105,1,-1,"O/U capacity (kW)"},\n'
            '//{0x10,0,217,1,-1,"Operation Mode"},\n'
            '//{0x10,1,307,1,-1,"Thermostat ON/OFF"},',
            output_text=False
        )

        self.assertEqual(
            {
                (3, 64, 0): [
                    CommandDecoder(14, decoding.decode_byte_1, '00.11.152', 'O/U MPU ID (yy)'),
                    CommandDecoder(15, decoding.decode_byte_10, '00.12.105', 'O/U capacity (kW)'),
                ],
                (3, 64, 16): [
                    CommandDecoder(3, espaltherma.decode_operation_mode, '10.0.217', 'Operation Mode'),
                    CommandDecoder(4, decoding.decode_bits[7], '10.1.307', 'Thermostat ON/OFF'),
                ],
            }, result
        )
