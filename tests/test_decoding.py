""" Tests for the functions in the decoding module.

Those functions decode response packets into Altherma attribute values.
"""

import unittest

from collections import defaultdict
from more_itertools import bucket, one

from pytherma import decoding


class DecodingTest(unittest.TestCase):
    """ Tests decoding of packets into Altherma attribute values. """

    def test_cases(self):
        """ Tests that several real examples of raw captured packets are decoded correctly. """
        # https://docs.google.com/spreadsheets/d/1N-dWh0dZiMOZL8hpl0bA1vJ3OUGyg2zsdQAbUX_rVcw/edit?usp=sharing
        # 1252,1263 22:46:00.2408396 [(7, 61, 39)] (61 => 39)
        values = decoding.decode(bytes([3, 64, 33, 155]),
                                 bytes([64, 33, 18, 5, 0, 0, 0, 39, 0, 0, 160, 0, 0, 0, 0, 0, 0,
                                        0, 0, 192]))
        self.assertEqual(39, values[65][1], "Wrong decode for 65:Voltage (N-phase) (V)")

        # 15000,15011 22:47:50.3817713 [(5, 116, 115)] (37.2 => 37.1)
        values = decoding.decode(bytes([3, 64, 97, 91]),
                                 bytes([64, 97, 18, 128, 0, 115, 1, 109, 1, 30, 1, 61, 1, 22, 2,
                                        250, 0, 0, 0, 123]))
        self.assertEqual(37.1, values[144][1],
                         "Wrong decode for 144:Leaving water temp. before BUH (R1T)(C)")

        # 4008,4019 22:46:21.4443689 [(7, 112, 111)] (36.8 => 36.7)
        values = decoding.decode(bytes([3, 64, 97, 91]),
                                 bytes([64, 97, 18, 128, 0, 116, 1, 111, 1, 37, 1, 67, 1, 18, 2,
                                        250, 0, 0, 0, 111]))
        self.assertEqual(37.2, values[144][1],
                         "Wrong decode for 144:Leaving water temp. before BUH (R1T)(C)")
        self.assertEqual(36.7, values[145][1],
                         "Wrong decode for 145:Leaving water temp. after BUH (R2T)(C)")
        self.assertEqual(29.3, values[146][1],
                         "Wrong decode for 146:Refrig. Temp. liquid side (R3T)(C)")
        self.assertEqual(32.3, values[147][1],
                         "Wrong decode for 147:Inlet water temp.(R4T)(C)")
        self.assertEqual(53.0, values[148][1],
                         "Wrong decode for 148:DHW tank temp. (R5T)(C)")

        # 5882,5893 22:46:35.4596000 [(5, 128, 144)] (bit 4 OFF => ON)
        values = decoding.decode(bytes([3, 64, 98, 90]),
                                 bytes([64, 98, 19, 128, 0, 144, 94, 1, 210, 0, 0, 1, 253,
                                        255, 0, 100, 0, 0, 0, 0, 168]))
        self.assertEqual(True, values[156][1],
                         "Wrong decode for 156:Powerful DHW Operation. ON/OFF")

        # 25864,25875 22:49:20.4284707 [(10, 0, 16)] (bit 4 OFF => ON)
        # 25864,25875 22:49:20.4284707 [(15, 100, 94)] (100 => 94)
        values = decoding.decode(bytes([3, 64, 98, 90]),
                                 bytes([64, 98, 19, 128, 0, 144, 94, 1, 210, 0, 16, 1, 253,
                                        255, 0, 94, 0, 0, 0, 0, 158]))
        self.assertEqual(True, values[166][1], "Wrong decode for 166:Main RT Heating")
        self.assertEqual(94, values[181][1],
                         "Wrong decode for 181:Water pump signal (0:max-100:stop)")

    def test_overlap(self):
        """ Tests that decoders do not overlap.

        If a byte of the response is processed by a bit decoder, then it can only be processed
        by bit decoders, and for different bits (multiple decoders may not test the same bits).

        If a byte of the response is processed by another decoder (byte, word or longer) then
        it may only be tested by a single decoder.
        """
        command_decoders = bucket(decoding.command_decoders, lambda decoder: decoder.prefix)
        for command in command_decoders:
            decoders = command_decoders[command]
            non_bit_tested_byte_to_decoder = {}
            bit_tested_bytes_to_bit_to_decoders = defaultdict(dict)

            for decoder in decoders:
                tested_bits = {i for i, decode_fn in decoding.decode_bits.items()
                               if decode_fn is decoder.decode_fn}
                self.assertIn(len(tested_bits), [0, 1])
                if len(tested_bits) == 1:
                    tested_byte = decoder.start_position
                    overlapping_decoder = non_bit_tested_byte_to_decoder.get(tested_byte)
                    self.assertIsNone(overlapping_decoder,
                                      f"{decoder} and {overlapping_decoder} overlap on {command} "
                                      f"byte {tested_byte}")

                    tested_bit = one(tested_bits)
                    overlapping_decoder = (
                        bit_tested_bytes_to_bit_to_decoders[tested_byte].get(tested_bit)
                    )
                    self.assertIsNone(overlapping_decoder,
                                      f"{decoder} overlaps on {command} byte {tested_byte} "
                                      f"bit {tested_bit}")

                    bit_tested_bytes_to_bit_to_decoders[tested_byte][tested_bit] = decoder
                else:
                    overlapping_decoders = {
                        other_decoder
                        for position, other_decoder in bit_tested_bytes_to_bit_to_decoders.items()
                        if (position <  decoder.end_position and
                            position >= decoder.start_position)
                    }
                    self.assertEqual(set(), overlapping_decoders,
                                     f"{decoder} and {overlapping_decoders} overlap on {command} "
                                     f"bytes {decoder.start_position}-{decoder.end_position - 1}")

                    overlapping_decoders = {
                        other_decoder
                        for position, other_decoder in non_bit_tested_byte_to_decoder.items()
                        if (position <  decoder.end_position and
                            position >= decoder.start_position)
                    }
                    self.assertEqual(set(), overlapping_decoders,
                                     f"{decoder} overlaps on {command} bytes "
                                     f"{decoder.start_position}-{decoder.end_position - 1}")

                    for i in range(decoder.start_position, decoder.end_position):
                        non_bit_tested_byte_to_decoder[i] = decoder
