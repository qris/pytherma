""" Tests for the functions in the decoding module.

Those functions decode response packets into Altherma attribute values.
"""

import unittest

from collections import defaultdict
from more_itertools import one

from pytherma import comms, decoding
from pytherma.decoding import P1P2Variable


class DecodingTest(unittest.TestCase):
    """ Tests decoding of packets into Altherma attribute values. """

    def test_decode_page_0(self):
        """ Tests that the contents of page 0 are decoded correctly, using raw captured packets. """
        # https://docs.google.com/spreadsheets/d/1N-dWh0dZiMOZL8hpl0bA1vJ3OUGyg2zsdQAbUX_rVcw/edit?usp=sharing

        # 2020/06/01 22:51:45:
        # 19:O/U MPU ID (xx): 4 => 0;
        # 20:O/U MPU ID (yy): 57 => 0;
        # 21:O/U capacity (kW): 6 => 0;
        # Assuming these:
        # 43048,43058 22:51:45.0380990 [(3, 4, 0), (14, 57, 0), (15, 60, 0)]
        values = decoding.decode_serial(
            bytes([3, 64, 0, 188]),
            bytes([64, 0, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 176]))
        self.assertEqual(0, values[19][1], "Wrong decode for 19:O/U MPU ID (xx)")
        self.assertEqual(0, values[20][1], "20:O/U MPU ID (yy)")
        self.assertEqual(0.0, values[21][1], "21:O/U capacity (kW)")

        # 46692,46703 22:52:15.0381757 [(13, 0, 4), (14, 0, 57), (16, 104, 43)]
        values = decoding.decode_serial(
            bytes([3, 64, 0, 188]),
            bytes([64, 0, 15, 4, 1, 0, 1, 1, 1, 0, 2, 1, 1, 4, 57, 60, 43]))
        self.assertEqual(4, values[19][1], "Wrong decode for 19:O/U MPU ID (xx)")
        self.assertEqual(57, values[20][1], "20:O/U MPU ID (yy)")
        self.assertEqual(6.0, values[21][1], "21:O/U capacity (kW)")

    def test_decode_page_16(self):
        """ Tests that the contents of page 16 are decoded correctly, using raw captured packets. """
        # 27304,27315 22:49:35.0694571 [(3, 0, 1), (19, 87, 86)]
        values = decoding.decode_serial(
            bytes([3, 64, 16, 172]),
            bytes([64, 16, 18, 1, 0, 0, 0, 0, 0, 67, 3, 0, 0, 0, 0, 0, 0, 0, 0, 86]))
        self.assertEqual(True, values[22][1], "Wrong decode for 22:Operation Mode (Heating)")

        # 41294,41305 22:51:30.0844895 [(3, 1, 0), (19, 86, 87)]
        # [[3, 64, 16, 172], [64, 16, 18, 0, 0, 0, 0, 0, 0, 67, 3, 0, 0, 0, 0, 0, 0, 0, 0, 87]]
        values = decoding.decode_serial(
            bytes([3, 64, 16, 172]),
            bytes([64, 16, 18, 0, 0, 0, 0, 0, 0, 67, 3, 0, 0, 0, 0, 0, 0, 0, 0, 87]))
        self.assertEqual(False, values[22][1], "Wrong decode for 22:Operation Mode (Heating)")

    def test_decode_page_17(self):
        """ Tests that the contents of page 17 are decoded correctly, using raw captured packets. """
        # 2020/06/01 22:51:45:
        # 47:O/U EEPROM (1st digit): 2 => 0
        # 48:O/U EEPROM (3rd 4th digit): 31 => 0
        # 49:O/U EEPROM (5th 6th digit): 95 => 0
        # 50:O/U EEPROM (7th 8th digit): 1 => 0
        # 51:O/U EEPROM (10th digit): 2 => 0
        # 52:O/U EEPROM (11th digit): E => ''
        # Assumed to be BCD encoded in (seems likely):
        # 43166,43177 22:51:45.1314069 [(3, 2, 0), (4, 49, 0), (5, 149, 0), (6, 1, 0), (7, 2, 0), (8, 5, 0)]
        # [[3, 64, 17, 171], [64, 17, 8, 0, 0, 0, 0, 0, 0, 166]]
        # 47418,47429 22:52:20.1469529 [(3, 0, 2), (4, 0, 49), (5, 0, 149), (6, 0, 1), (7, 0, 2), (8, 0, 5)]
        # [[3, 64, 17, 171], [64, 17, 8, 2, 49, 149, 1, 2, 5, 214]]
        # I'm guessing that O/U means Outdoor Unit.
        values = decoding.decode_serial(
            bytes([3, 64, 17, 171]),
            bytes([64, 17, 8, 0, 0, 0, 0, 0, 0, 166]))
        self.assertEqual(0, values[47][1], "Wrong decode for 47:O/U EEPROM (1st digit)")
        self.assertEqual(0, values[48][1], "Wrong decode for 48:O/U EEPROM (3rd 4th digit)")
        self.assertEqual(0, values[49][1], "Wrong decode for 49:O/U EEPROM (5th 6th digit)")
        self.assertEqual(0, values[50][1], "Wrong decode for 50:O/U EEPROM (7th 8th digit)")
        self.assertEqual(0, values[51][1], "Wrong decode for 51:O/U EEPROM (10th digit)")
        self.assertEqual(0, values[52][1], "Wrong decode for 52:O/U EEPROM (11th digit)")
        values = decoding.decode_serial(
            bytes([3, 64, 17, 171]),
            bytes([64, 17, 8, 2, 49, 149, 1, 2, 5, 214]))
        self.assertEqual(0x2, values[47][1], "Wrong decode for 47:O/U EEPROM (1st digit)")
        self.assertEqual(0x31, values[48][1], "Wrong decode for 48:O/U EEPROM (3rd 4th digit)")
        self.assertEqual(0x95, values[49][1], "Wrong decode for 49:O/U EEPROM (5th 6th digit)")
        self.assertEqual(0x1, values[50][1], "Wrong decode for 50:O/U EEPROM (7th 8th digit)")
        self.assertEqual(0x2, values[51][1], "Wrong decode for 51:O/U EEPROM (10th digit)")
        self.assertEqual(0x5, values[52][1], "Wrong decode for 52:O/U EEPROM (11th digit)")

    def test_decode_page_32(self):
        """ Tests that the contents of page 32 are decoded correctly, using raw captured packets. """
        # 2020/06/01 22:51:45: 33:Target Evap. Temp.(C): 32.6 => 0
        # 2020/06/01 22:52:15: 33:Target Evap. Temp.(C): 0 => 32.6
        # Assuming these:
        # 43204,43215 22:51:45.1785851 [(7, 74, 0), (8, 1, 0)]
        # [[3, 64, 32, 156], [64, 32, 19, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 139]]
        # 46240,46251 22:52:10.1786246 [(7, 0, 69), (8, 0, 1)]
        # [[3, 64, 32, 156], [64, 32, 19, 165, 0, 0, 0, 69, 1, 0, 0, 150, 0, 0, 0, 215, 0, 115, 0, 1, 192]]
        values = decoding.decode_serial(
            bytes([3, 64, 32, 156]),
            bytes([64, 32, 19, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 139]))
        self.assertEqual(0, values[56][1], "Wrong decode for 56:Discharge pipe temp.(C)")
        values = decoding.decode_serial(
            bytes([3, 64, 32, 156]),
            bytes([64, 32, 19, 165, 0, 0, 0, 69, 1, 0, 0, 150, 0, 0, 0, 215, 0, 115, 0, 1, 192]))
        self.assertEqual(32.5, values[56][1], "Wrong decode for 56:Discharge pipe temp.(C)")
        self.assertEqual(16.5, values[54][1], "Wrong decode for 54:Outdoor air temp.(R1T)(C)")
        # 2020/06/01 22:51:35: 54:Outdoor air temp.(R1T)(C): 16.5 => 16.0
        # Assumed to be:
        # 41992,42003 22:51:35.1785402 [(3, 165, 160), (20, 202, 207)]
        # [[3, 64, 32, 156], [64, 32, 19, 160, 0, 0, 0, 74, 1, 0, 0, 150, 0, 0, 0, 200, 0, 115, 0, 1, 207]]
        values = decoding.decode_serial(
            bytes([3, 64, 32, 156]),
            bytes([64, 32, 19, 160, 0, 0, 0, 74, 1, 0, 0, 150, 0, 0, 0, 200, 0, 115, 0, 1, 207]))
        self.assertEqual(16.0, values[54][1], "Wrong decode for 54:Outdoor air temp.(R1T)(C)")
        self.assertEqual(11.5, values[61][1], "Wrong decode for 61:Pressure(kgcm2)")

        # 2020/06/01 22:51:05: 61:Pressure(kgcm2): 11.5 => 11.7
        # Assumed to be:
        # 37764,37775 22:51:00.1786083 [(11, 155, 150), (17, 115, 117), (20, 197, 200)]
        # [[3, 64, 32, 156], [64, 32, 19, 165, 0, 0, 0, 74, 1, 0, 0, 150, 0, 0, 0, 200, 0, 117, 0, 1, 200]]
        values = decoding.decode_serial(
            bytes([3, 64, 32, 156]),
            bytes([64, 32, 19, 165, 0, 0, 0, 74, 1, 0, 0, 150, 0, 0, 0, 200, 0, 117, 0, 1, 200]))
        self.assertEqual(16.5, values[54][1], "Wrong decode for 54:Outdoor air temp.(R1T)(C)")
        self.assertEqual(15.0, values[58][1], "Wrong decode for 58:Heat exchanger mid-temp.(C)")
        self.assertEqual(11.7, values[61][1], "Wrong decode for 61:Pressure(kgcm2)")

    def test_decode_page_33(self):
        """ Tests that the contents of page 33 are decoded correctly, using raw captured packets. """
        # 1252,1263 22:46:00.2408396 [(7, 61, 39)] (61 => 39)
        values = decoding.decode_serial(
            bytes([3, 64, 33, 155]),
            bytes([64, 33, 18, 5, 0, 0, 0, 39, 0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0, 192]))
        self.assertEqual(39, values[65][1], "Wrong decode for 65:Voltage (N-phase) (V)")

        # 2020/06/01 22:48:35: 58:Heat exchanger mid-temp.(C): 16 => 15.5'C
        # 2020/06/01 22:51:05: 58:Heat exchanger mid-temp.(C): 15.5 => 15'C
        # Assumed to be (seems very likely):
        # 21402,21413 22:48:45.2095790 [(10, 160, 155), (19, 193, 198)]
        # [[3, 64, 33, 155], [64, 33, 18, 5, 0, 0, 0, 38, 0, 0, 155, 0, 0, 0, 0, 0, 0, 0, 0, 198]]
        values = decoding.decode_serial(
            bytes([3, 64, 33, 155]),
            bytes([64, 33, 18, 5, 0, 0, 0, 38, 0, 0, 155, 0, 0, 0, 0, 0, 0, 0, 0, 198]))
        # self.assertEqual(15.5, values[58][1], "Wrong decode for 58:Heat exchanger mid-temp.(C)")
        # 37832,37843 22:51:00.2409211 [(10, 155, 150), (19, 244, 249)]
        # [[3, 64, 33, 155], [64, 33, 18, 5, 0, 0, 0, 248, 0, 0, 150, 0, 0, 0, 0, 0, 0, 0, 0, 249]]
        values = decoding.decode_serial(
            bytes([3, 64, 33, 155]),
            bytes([64, 33, 18, 5, 0, 0, 0, 248, 0, 0, 150, 0, 0, 0, 0, 0, 0, 0, 0, 249]))
        # self.assertEqual(15.0, values[58][1], "Wrong decode for 58:Heat exchanger mid-temp.(C)")

        # 2020/06/01 22:51:45: 63:INV primary current (A): 0.5 => 0
        # Assumed to be:
        # 43272,43283 22:51:45.2409813 [(3, 5, 0), (7, 243, 0), (10, 150, 0), (19, 254, 140)]
        # [[3, 64, 33, 155], [64, 33, 18, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 140]]
        self.assertEqual(0.5, values[63][1], "Wrong decode for 63:INV primary current (A)")
        values = decoding.decode_serial(
            bytes([3, 64, 33, 155]),
            bytes([64, 33, 18, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 140]))
        self.assertEqual(0.0, values[63][1], "Wrong decode for 63:INV primary current (A)")

    def test_decode_page_48(self):
        """ Tests that the contents of page 48 are decoded correctly, using raw captured packets. """
        values = decoding.decode_serial(
            bytes([3, 64, 48, 140]),
            bytes([64, 48, 13, 0, 0, 0, 194, 1, 0, 0, 128, 0, 0, 0, 63]))
        # 2020/06/01 22:51:45: 89:Expansion valve (pls): 450 => 0
        # Assumed to be:
        # 43330,43341 22:51:45.2880632 [(6, 194, 0), (7, 1, 0), (14, 191, 130)]
        # [[3, 64, 48, 140], [64, 48, 13, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 130]]
        self.assertEqual(450, values[89][1],
                         "Wrong decode for 89:Expansion valve (pls)")
        values = decoding.decode_serial(
            bytes([3, 64, 48, 140]),
            bytes([64, 48, 13, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 130]))
        self.assertEqual(0, values[89][1],
                         "Wrong decode for 89:Expansion valve (pls)")

    def test_decode_page_96(self):
        """ Tests that the contents of page 96 are decoded correctly, using raw captured packets. """
        # 3948,3959 22:46:21.2253022 [(1, 0, 96), (2, 0, 19), (3, 0, 128), (4, 71, 0), (5, 38, 64), (6, 2, 0), (7, 250, 0), (9, 160, 71), (10, 0, 38), (11, 27, 2), (12, 242, 250), (13, 118, 0), (14, 0, 160), (16, 64, 27), (17, 96, 242), (18, 19, 118), (19, 128, 0), (21, 64, None), (22, 0, None), (23, 0, None), (24, 0, None), (25, 71, None), (26, 38, None), (27, 2, None), (28, 250, None), (29, 0, None), (30, 160, None), (31, 0, None), (32, 27, None), (33, 242, None), (34, 118, None), (35, 0, None), (36, 0, None)]
        values = decoding.decode_serial(
            bytes([3, 64, 96, 92]),
            bytes([64, 96, 19, 128, 0, 64, 0, 0, 0, 71, 38, 2, 250, 0, 160, 0, 27, 242, 118, 0, 0]))
        self.assertEqual(False, values[132][1],
                         "Wrong decode for 132:BSH")

        # 6356,6367 22:46:40.3344872 [(15, 0, 32)]
        values = decoding.decode_serial(
            bytes([3, 64, 96, 92]),
            bytes([64, 96, 19, 128, 0, 64, 0, 0, 0, 71, 38, 2, 250, 0, 160, 32, 27, 242, 118, 0, 224]))
        self.assertEqual(True, values[132][1],
                         "Wrong decode for 132:BSH")

        # 16708,16719 22:48:05.3346454 [(15, 32, 0), (20, 224, 0)]
        values = decoding.decode_serial(
            bytes([3, 64, 96, 92]),
            bytes([64, 96, 19, 128, 0, 64, 0, 0, 0, 71, 38, 2, 250, 0, 160, 0, 27, 242, 118, 0, 0]))
        self.assertEqual(False, values[132][1],
                         "Wrong decode for 132:BSH")

    def test_decode_page_97(self):
        """ Tests that the contents of page 97 are decoded correctly, using raw captured packets. """
        # 15000,15011 22:47:50.3817713 [(5, 116, 115)] (37.2 => 37.1)
        values = decoding.decode_serial(
            bytes([3, 64, 97, 91]),
            bytes([64, 97, 18, 128, 0, 115, 1, 109, 1, 30, 1, 61, 1, 22, 2, 250, 0, 0, 0, 123]))
        self.assertEqual(37.1, values[144][1],
                         "Wrong decode for 144:Leaving water temp. before BUH (R1T)(C)")

        # 4008,4019 22:46:21.4443689 [(7, 112, 111)] (36.8 => 36.7)
        values = decoding.decode_serial(
            bytes([3, 64, 97, 91]),
            bytes([64, 97, 18, 128, 0, 116, 1, 111, 1, 37, 1, 67, 1, 18, 2, 250, 0, 0, 0, 111]))
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

    def test_decode_page_98(self):
        """ Tests that the contents of page 98 are decoded correctly, using raw captured packets. """
        # 5882,5893 22:46:35.4596000 [(5, 128, 144)] (bit 4 OFF => ON)
        values = decoding.decode_serial(
            bytes([3, 64, 98, 90]),
            bytes([64, 98, 19, 128, 0, 144, 94, 1, 210, 0, 0, 1, 253, 255, 0, 100, 0, 0, 0, 0, 168]))
        self.assertEqual(True, values[156][1],
                         "Wrong decode for 156:Powerful DHW Operation. ON/OFF")
        self.assertEqual(35.0, values[161][1],
                         "Wrong decode for 161:LW setpoint (add)(C)")
        self.assertEqual(21.0, values[162][1],
                         "Wrong decode for 162:RT setpoint(C)")
        self.assertEqual(False, values[166][1],
                         "Wrong decode for 166:Main RT Heating")

        # 2020/06/01 22:51:45: 153:Reheat ON/OFF: 1 => 0
        # 2020/06/01 22:52:35: 153:Reheat ON/OFF: 0 => 0
        # Assumed to be:
        # 43514,43525 22:51:45.4443617 [(5, 144, 0)]
        # [[3, 64, 98, 90], [64, 98, 19, 128, 0, 0, 131, 1, 210, 0, 0, 0, 253, 255, 0, 100, 0, 0, 0, 0, 20]]
        # 49574,49585 22:52:35.4444182 [(5, 0, 128)]
        # [3, 64, 98, 90], [64, 98, 19, 128, 0, 128, 94, 1, 210, 0, 0, 1, 253, 255, 0, 100, 0, 0, 0, 0, 184]]
        values = decoding.decode_serial(
            bytes([3, 64, 98, 90]),
            bytes([64, 98, 19, 128, 0, 0, 131, 1, 210, 0, 0, 0, 253, 255, 0, 100, 0, 0, 0, 0, 20]))
        self.assertEqual(False, values[153][1],
                         "Wrong decode for 153:Reheat ON/OFF")
        self.assertEqual(False, values[156][1],
                         "Wrong decode for 156:Powerful DHW Operation. ON/OFF")
        self.assertEqual(38.7, values[161][1],
                         "Wrong decode for 161:LW setpoint (add)(C)")

        values = decoding.decode_serial(
            bytes([3, 64, 98, 90]),
            bytes([64, 98, 19, 128, 0, 128, 94, 1, 210, 0, 0, 1, 253, 255, 0, 100, 0, 0, 0, 0, 184]))
        self.assertEqual(True, values[153][1],
                         "Wrong decode for 153:Reheat ON/OFF")
        self.assertEqual(False, values[156][1],
                         "Wrong decode for 156:Powerful DHW Operation. ON/OFF")

        # 25864,25875 22:49:20.4284707 [(10, 0, 16)] (bit 4 OFF => ON)
        # 25864,25875 22:49:20.4284707 [(15, 100, 94)] (100 => 94)
        values = decoding.decode_serial(
            bytes([3, 64, 98, 90]),
            bytes([64, 98, 19, 128, 0, 144, 94, 1, 210, 0, 16, 1, 253, 255, 0, 94, 0, 0, 0, 0, 158]))
        self.assertEqual(True, values[166][1], "Wrong decode for 166:Main RT Heating")
        self.assertEqual(True, values[178][1], "Wrong decode for 178:Space H Operation output")
        self.assertEqual(94, values[181][1],
                         "Wrong decode for 181:Water pump signal (0:max-100:stop)")

        # 27710,27721 22:49:35.4283079 [(12, 72, 118), (20, 152, 106)]
        values = decoding.decode_serial(
            bytes([3, 64, 98, 90]),
            bytes([64, 98, 19, 128, 0, 144, 94, 1, 210, 0, 16, 1, 118, 0, 0, 24, 0, 0, 0, 0, 106]))
        self.assertEqual(True, values[156][1],
                         "Wrong decode for 156:Powerful DHW Operation. ON/OFF")
        self.assertEqual(True, values[166][1],
                         "Wrong decode for 166:Main RT Heating")
        self.assertEqual(11.8, values[179][1],
                         "Wrong decode for 179:Flow sensor (l/min)")

        # 43514,43525 22:51:45.4443617 [(5, 144, 0), (6, 94, 131), (11, 1, 0), (20, 168, 20)]
        # [[3, 64, 98, 90], [64, 98, 19, 128, 0, 0, 131, 1, 210, 0, 0, 0, 253, 255, 0, 100, 0, 0, 0, 0, 20]]
        values = decoding.decode_serial(
            bytes([3, 64, 98, 90]),
            bytes([64, 98, 19, 128, 0, 0, 131, 1, 210, 0, 0, 0, 253, 255, 0, 100, 0, 0, 0, 0, 20]))
        self.assertEqual(False, values[178][1], "Wrong decode for 178:Space H Operation output")
        self.assertEqual(-0.3, values[179][1],
                         "Wrong decode for 179:Flow sensor (l/min)")
        self.assertEqual(100, values[181][1],
                         "Wrong decode for 181:Water pump signal (0:max-100:stop)")

    def test_decode_page_99(self):
        """ Tests that the contents of page 99 are decoded correctly, using raw captured packets. """
        # 798,809 22:45:29.6316392
        # Assumed to be 194:Indoor Unit Address and 195-200:I/U EEPROM (BCD digits)
        # [[3, 64, 99, 89], [64, 99, 10, 128, 0, 1, 112, 100, 50, 21, 1, 181]]
        values = decoding.decode_serial(
            bytes([3, 64, 99, 89]),
            bytes([64, 99, 10, 128, 0, 1, 112, 100, 50, 21, 1, 181]))
        self.assertEqual(0, values[194][1],
                         "Wrong decode for 194:Indoor Unit Address")
        self.assertEqual(1, values[195][1],
                         "Wrong decode for 195:I/U EEPROM (3rd digit)"),
        self.assertEqual(0x70, values[196][1],
                         "Wrong decode for 196:I/U EEPROM (4th 5th digit)"),
        self.assertEqual(0x64, values[197][1],
                         "Wrong decode for 197:I/U EEPROM (6th 7th digit)"),
        self.assertEqual(0x32, values[198][1],
                         "Wrong decode for 198:I/U EEPROM (8th 9th digit)"),
        self.assertEqual(0x15, values[199][1],
                         "Wrong decode for 199:I/U EEPROM (11th digit)"),
        self.assertEqual(1, values[200][1],
                         "Wrong decode for 200:I/U EEPROM (12th digit)(rev.)"),

    def test_no_overlap(self):
        """ Tests that decoders do not overlap.

        If a byte of the response is processed by a bit decoder, then it can only be processed
        by bit decoders, and for different bits (multiple decoders may not test the same bits).

        If a byte of the response is processed by another decoder (byte, word or longer) then
        it may only be tested by a single decoder.
        """
        for prefix, decoders in decoding.serial_page_prefix_to_decoders.items():
            non_bit_tested_byte_to_decoder = {}
            bit_tested_bytes_to_bit_to_decoders = defaultdict(dict)

            for decoder in decoders:
                # Find out which, if any, of the decode_bits canned decoders are used,
                # i.e. which bits are tested by this decoder. This only works if we only
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

    def test_unique(self):
        """ Tests that each variable is only set by a single decoder.

        No two decoders should set the same variable, since the results are unpredictable, and
        this probably indicates a copy-and-paste error.
        """
        variable_number_to_decoders = defaultdict(list)

        for prefix, decoders in decoding.serial_page_prefix_to_decoders.items():
            for decoder in decoders:
                variable_number_to_decoders[decoder.number].append((prefix, decoder))

        for variable_number, decoders in list(variable_number_to_decoders.items()):
            if len(decoders) == 1:
                del variable_number_to_decoders[variable_number]

        self.assertEqual({}, dict(variable_number_to_decoders),
                         "These variables are set by more than one decoder")

    def assert_decode(self, page, offset, value_bytes, variable_number, expected_value, name=None):
        """ Test decoding of the specified value_bytes, on the specified page and offset.

        This abbreviates calling decoding.decode_serial and making assertions on the resulting mapping.
        """
        dummy_request_frame = bytes([3, 64, page])
        # We don't bother to make the response the correct (exact) length. We just include sufficient bytes that should satisfy
        # the decoder (as far as we've been told), and the mandatory checksum after them. If the decoder is not actually satisfied
        # then it will raise an exception.
        fake_length = 1 + offset + len(value_bytes) + 1
        dummy_response_frame = bytes([64, page, fake_length] + ([0] * offset) + value_bytes)
        dummy_response_frame += comms.calculate_checksum(dummy_response_frame)
        assert len(dummy_response_frame) == fake_length + 2

        values = decoding.decode_serial(dummy_request_frame, dummy_response_frame)
        failure_msg = f"Wrong decode for {variable_number}"
        if name is not None:
            failure_msg += ":" + name
        self.assertEqual(expected_value, values[variable_number][1], failure_msg)

    def test_decodes(self):
        """ Test that some values are decoded properly, using the abbreviated method, assert_decode. """
        self.assert_decode(98, 2, [144], 156, True, "Powerful DHW Operation. ON/OFF")

    def test_decode_p1p2(self):
        """ Test that decode_p1p2 correctly decodes some example messages. """
        # import pdb; pdb.set_trace()
        result = decoding.decode_p1p2(bytearray.fromhex("400010010081013700180015001A000000000000400000"))  # CRC=87
        self.assertEqual(True, result[P1P2Variable.heating_enabled][1])
        self.assertEqual(True, result[P1P2Variable.heating_on][1])
        self.assertEqual(False, result[P1P2Variable.cooling_on][1])
        self.assertEqual(False, result[P1P2Variable.main_zone][1])
        self.assertEqual(False, result[P1P2Variable.additional_zone][1])
        self.assertEqual(True, result[P1P2Variable.dhw_tank][1])
        self.assertEqual(True, result[P1P2Variable.threeway_on_off][1])
        self.assertEqual(False, result[P1P2Variable.threeway_tank][1])
        self.assertEqual(55, result[P1P2Variable.target_dhw_temp][1])
        self.assertEqual(21, result[P1P2Variable.target_room_temp][1])
        self.assertEqual(False, result[P1P2Variable.quiet_mode][1])
        self.assertEqual(False, result[P1P2Variable.compressor_on][1])
        self.assertEqual(False, result[P1P2Variable.pump_on][1])
        self.assertEqual(False, result[P1P2Variable.dhw_active][1])
