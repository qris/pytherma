""" Tests for the functions in the decoding module.

Those functions decode response packets into Altherma attribute values.
"""

import unittest

from collections import defaultdict
from more_itertools import one

from pytherma import decoding


class DecodingTest(unittest.TestCase):
    """ Tests decoding of packets into Altherma attribute values. """

    def test_cases(self):
        """ Tests that several real examples of raw captured packets are decoded correctly. """
        # https://docs.google.com/spreadsheets/d/1N-dWh0dZiMOZL8hpl0bA1vJ3OUGyg2zsdQAbUX_rVcw/edit?usp=sharing

        # 2020/06/01 22:51:45:
        # 19:O/U MPU ID (xx): 4 => 0;
        # 20:O/U MPU ID (yy): 57 => 0;
        # 21:O/U capacity (kW): 6 => 0;
        # Assuming these:
        # 43048,43058 22:51:45.0380990 [(3, 4, 0), (14, 57, 0), (15, 60, 0)]
        values = decoding.decode(bytes([3, 64, 0, 188]),
                                 bytes([64, 0, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 176]))
        self.assertEqual(0, values[19][1], "Wrong decode for 19:O/U MPU ID (xx)")
        self.assertEqual(0, values[20][1], "20:O/U MPU ID (yy)")
        self.assertEqual(0.0, values[21][1], "21:O/U capacity (kW)")

        # 46692,46703 22:52:15.0381757 [(13, 0, 4), (14, 0, 57), (16, 104, 43)]
        values = decoding.decode(bytes([3, 64, 0, 188]),
                                 bytes([64, 0, 15, 4, 1, 0, 1, 1, 1, 0, 2, 1, 1, 4, 57, 60, 43]))
        self.assertEqual(4, values[19][1], "Wrong decode for 19:O/U MPU ID (xx)")
        self.assertEqual(57, values[20][1], "20:O/U MPU ID (yy)")
        self.assertEqual(6.0, values[21][1], "21:O/U capacity (kW)")

        # 27304,27315 22:49:35.0694571 [(3, 0, 1), (19, 87, 86)]
        values = decoding.decode(bytes([3, 64, 16, 172]),
                                 bytes([64, 16, 18, 1, 0, 0, 0, 0, 0, 67, 3, 0, 0, 0, 0, 0,
                                       0, 0, 0, 86]))
        self.assertEqual(True, values[22][1], "Wrong decode for 22:Operation Mode (Heating)")

        # 41294,41305 22:51:30.0844895 [(3, 1, 0), (19, 86, 87)]
        [[3, 64, 16, 172], [64, 16, 18, 0, 0, 0, 0, 0, 0, 67, 3, 0, 0, 0, 0, 0, 0, 0, 0, 87]]
        values = decoding.decode(bytes([3, 64, 16, 172]),
                                 bytes([64, 16, 18, 0, 0, 0, 0, 0, 0, 67, 3, 0, 0, 0, 0, 0,
                                        0, 0, 0, 87]))
        self.assertEqual(False, values[22][1], "Wrong decode for 22:Operation Mode (Heating)")

        # 1252,1263 22:46:00.2408396 [(7, 61, 39)] (61 => 39)
        values = decoding.decode(bytes([3, 64, 33, 155]),
                                 bytes([64, 33, 18, 5, 0, 0, 0, 39, 0, 0, 160, 0, 0, 0, 0, 0, 0,
                                        0, 0, 192]))
        self.assertEqual(39, values[65][1], "Wrong decode for 65:Voltage (N-phase) (V)")

        # 42720,42731 22:51:40.2882745 [(10, 128, 0), (14, 63, 191)]
        # [[3, 64, 48, 140], [64, 48, 13, 0, 0, 0, 194, 1, 0, 0, 0, 0, 0, 0, 191]]
        values = decoding.decode(bytes([3, 64, 48, 140]),
                                 bytes([64, 48, 13, 0, 0, 0, 194, 1, 0, 0, 0, 0, 0, 0, 191]))
        self.assertEqual(False, values[153][1],
                         "Wrong decode for 153:Reheat ON/OFF")
        values = decoding.decode(bytes([3, 64, 48, 140]),
                                 bytes([64, 48, 13, 0, 0, 0, 194, 1, 0, 0, 128, 0, 0, 0, 63]))
        self.assertEqual(True, values[153][1],
                         "Wrong decode for 153:Reheat ON/OFF")

        # 3948,3959 22:46:21.2253022 [(1, 0, 96), (2, 0, 19), (3, 0, 128), (4, 71, 0), (5, 38, 64), (6, 2, 0), (7, 250, 0), (9, 160, 71), (10, 0, 38), (11, 27, 2), (12, 242, 250), (13, 118, 0), (14, 0, 160), (16, 64, 27), (17, 96, 242), (18, 19, 118), (19, 128, 0), (21, 64, None), (22, 0, None), (23, 0, None), (24, 0, None), (25, 71, None), (26, 38, None), (27, 2, None), (28, 250, None), (29, 0, None), (30, 160, None), (31, 0, None), (32, 27, None), (33, 242, None), (34, 118, None), (35, 0, None), (36, 0, None)]
        values = decoding.decode(bytes([3, 64, 96, 92]),
                                 bytes([64, 96, 19, 128, 0, 64, 0, 0, 0, 71, 38, 2, 250, 0, 160,
                                        0, 27, 242, 118, 0, 0]))
        self.assertEqual(False, values[132][1],
                         "Wrong decode for 132:BSH")

        # 6356,6367 22:46:40.3344872 [(15, 0, 32)]
        values = decoding.decode(bytes([3, 64, 96, 92]),
                                 bytes([64, 96, 19, 128, 0, 64, 0, 0, 0, 71, 38, 2, 250, 0, 160,
                                        32, 27, 242, 118, 0, 224]))
        self.assertEqual(True, values[132][1],
                         "Wrong decode for 132:BSH")

        # 16708,16719 22:48:05.3346454 [(15, 32, 0), (20, 224, 0)]
        values = decoding.decode(bytes([3, 64, 96, 92]),
                                 bytes([64, 96, 19, 128, 0, 64, 0, 0, 0, 71, 38, 2, 250, 0, 160,
                                        0, 27, 242, 118, 0, 0]))
        self.assertEqual(False, values[132][1],
                         "Wrong decode for 132:BSH")

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
        self.assertEqual(35.0, values[161][1],
                         "Wrong decode for 161:LW setpoint (add)(C)")
        self.assertEqual(21.0, values[162][1],
                         "Wrong decode for 162:RT setpoint(C)")

        # 25864,25875 22:49:20.4284707 [(10, 0, 16)] (bit 4 OFF => ON)
        # 25864,25875 22:49:20.4284707 [(15, 100, 94)] (100 => 94)
        values = decoding.decode(bytes([3, 64, 98, 90]),
                                 bytes([64, 98, 19, 128, 0, 144, 94, 1, 210, 0, 16, 1, 253,
                                        255, 0, 94, 0, 0, 0, 0, 158]))
        self.assertEqual(True, values[166][1], "Wrong decode for 166:Main RT Heating")
        self.assertEqual(True, values[178][1], "Wrong decode for 178:Space H Operation output")
        self.assertEqual(94, values[181][1],
                         "Wrong decode for 181:Water pump signal (0:max-100:stop)")

        # 27710,27721 22:49:35.4283079 [(12, 72, 118), (20, 152, 106)]
        values = decoding.decode(bytes([3, 64, 98, 90]),
                                 bytes([64, 98, 19, 128, 0, 144, 94, 1, 210, 0, 16, 1, 118, 0,
                                        0, 24, 0, 0, 0, 0, 106]))
        self.assertEqual(11.8, values[179][1],
                         "Wrong decode for 179:Flow sensor (l/min)")

        # 43514,43525 22:51:45.4443617 [(5, 144, 0), (6, 94, 131), (11, 1, 0), (20, 168, 20)]
        # [[3, 64, 98, 90], [64, 98, 19, 128, 0, 0, 131, 1, 210, 0, 0, 0, 253, 255, 0, 100, 0, 0, 0, 0, 20]]
        values = decoding.decode(bytes([3, 64, 98, 90]),
                                 bytes([64, 98, 19, 128, 0, 0, 131, 1, 210, 0, 0, 0, 253, 255,
                                        0, 100, 0, 0, 0, 0, 20]))
        self.assertEqual(False, values[178][1], "Wrong decode for 178:Space H Operation output")
        self.assertEqual(-0.3, values[179][1],
                         "Wrong decode for 179:Flow sensor (l/min)")
        self.assertEqual(100, values[181][1],
                         "Wrong decode for 181:Water pump signal (0:max-100:stop)")

    def test_overlap(self):
        """ Tests that decoders do not overlap.

        If a byte of the response is processed by a bit decoder, then it can only be processed
        by bit decoders, and for different bits (multiple decoders may not test the same bits).

        If a byte of the response is processed by another decoder (byte, word or longer) then
        it may only be tested by a single decoder.
        """
        for prefix, decoders in decoding.prefix_to_decoders.items():
            non_bit_tested_byte_to_decoder = {}
            bit_tested_bytes_to_bit_to_decoders = defaultdict(dict)

            for decoder in decoders:
                # Find out which, if any, of the decode_bits canned decoders are used,
                # i.e. whjch bits are tested by this decoder. This only works if we only
                # use the canned decoders!
                tested_bits = {i for i, decode_fn in decoding.decode_bits.items()
                               if decode_fn is decoder.decode_fn}

                # We assume that if no decode_bits decoders are used, the decoder must process
                # entire bytes, and thus conflict with any other decoder that processes the
                # same bytes:
                self.assertIn(len(tested_bits), [0, 1])

                if len(tested_bits) == 1:
                    # Which bits is it testing? Ensure that it doesn't overlap any decoder
                    # that we've already checked, and allocate those bits to this one:
                    tested_byte = decoder.start_position
                    overlapping_decoder = non_bit_tested_byte_to_decoder.get(tested_byte)
                    self.assertIsNone(overlapping_decoder,
                                      f"{decoder} and {overlapping_decoder} overlap on {prefix} "
                                      f"byte {tested_byte}")

                    tested_bit = one(tested_bits)
                    overlapping_decoder = (
                        bit_tested_bytes_to_bit_to_decoders[tested_byte].get(tested_bit)
                    )
                    self.assertIsNone(overlapping_decoder,
                                      f"{decoder} overlaps on {prefix} byte {tested_byte} "
                                      f"bit {tested_bit}")

                    bit_tested_bytes_to_bit_to_decoders[tested_byte][tested_bit] = decoder
                else:
                    # Which bytes is it testing? Ensure that it doesn't overlap any decoder
                    # that we've already checked, and allocate those bytes to this one:
                    overlapping_decoders = {
                        other_decoder
                        for position, other_decoder in bit_tested_bytes_to_bit_to_decoders.items()
                        if (position <  decoder.end_position and
                            position >= decoder.start_position)
                    }
                    self.assertEqual(set(), overlapping_decoders,
                                     f"{decoder} and {overlapping_decoders} overlap on {prefix} "
                                     f"bytes {decoder.start_position}-{decoder.end_position - 1}")

                    overlapping_decoders = {
                        other_decoder
                        for position, other_decoder in non_bit_tested_byte_to_decoder.items()
                        if (position <  decoder.end_position and
                            position >= decoder.start_position)
                    }
                    self.assertEqual(set(), overlapping_decoders,
                                     f"{decoder} overlaps on {prefix} bytes "
                                     f"{decoder.start_position}-{decoder.end_position - 1}")

                    for i in range(decoder.start_position, decoder.end_position):
                        non_bit_tested_byte_to_decoder[i] = decoder
