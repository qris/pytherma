""" Functions that decode a Daikin Altherma's response packet.

Most commands retrieve a set of variables. E.g. the command (3, 64, 97) might mean
"read register page 97". We don't know what it actually means because the commands
are not publicly documented.

The response consists of the following bytes:
[64, 97]: here is page 97.
[18]: the response has 18 bytes, not including the leading [64] or the trailing checksum.
[128, 0, 78, 1, 10, 1, 11, 1, 17, 1, 18, 2, 4, 1, 0, 0]: register values, to be decoded.
[59]: trailing checksum, which can be checked using comms.calculate_checksum(response).

The following types of register values are known:
* Byte with boolean (on/off) values in its bits (see decode_bit).
* Byte interpreted as an unsigned integer (0-255, see decode_byte).
* Two bytes (one word) interpreted as an unsigned integer (0-65535, see decode_word).

Commands must have decoders to extract information from the register values. These are
CommandDecoder instances, which have the following properties:

* The offset of the first byte to which the decoder applies (start_position). The length
  is determined by the decoder function (specifically its decode_len attribute).
  E.g. decode_word with an offset of 7 consumes bytes 7 and 8.
* The decoder function (decode_fn), e.g. decode_byte_1. Must take a single argument,
  which will be passed decode_fn.decode_len bytes of the response packet, starting from
  the offset (start_position). For example, decode_word (which has a decode_len of 2)
  with an offset of 7 will be passed response[7:8]. Therefore generic decoders
  (such as decode_byte) must be wrapped to supply the initial arguments (divisor), e.g.
  using partial or the canned shortcuts (decode_bits[4], decode_word_10, etc).
* The corresponding "variable number" in D-Checker, displayed in the user interface and
  in the column heading of the CSV export (see contrib/1_20200601-224524.csv for
  examples).
* The description of the variable, which may also be in the CSV header, possibly modified
  for readability (e.g. "Voltage (N-phase) (V)")

Unsigned integers (especially words) are often scaled by 10 to accommodate fixed point
real numbers, e.g. the value 273 means 27.3. The decode_word_10 shortcut handles this.
No scaled byte values are known, so you probably want to use decode_byte_1.
"""

import struct

from collections import namedtuple
from functools import partial
from more_itertools import one


def decode_bit(bit, data_bytes):
    """ Extract one bit from the specified response byte, returns a bool. """
    if len(data_bytes) == 1:
        return bool(data_bytes[0] & (1 << bit))
    else:
        return None


decode_bits = {
    i: partial(decode_bit, i)
    for i in range(8)
}

for decode_bits_fn in decode_bits.values():
    decode_bits_fn.decode_len = 1


def decode_byte(divisor, data_bytes):
    """ Extract one byte from the specified response byte, returns an integer. """
    if len(data_bytes) == 1:
        return data_bytes[0] / divisor
    else:
        return None


decode_byte_1 = partial(decode_byte, 1)
decode_byte_1.decode_len = 1

decode_byte_10 = partial(decode_byte, 10)
decode_byte_10.decode_len = 1


def decode_word(divisor, data_bytes):
    """ Extract two bytes from the specified response byte, returns an integer. """
    if len(data_bytes) == 2:
        # return ((data_bytes[1] * 256) + data_bytes[0]) / divisor
        return one(struct.unpack('<h', data_bytes)) / divisor
    else:
        return None


decode_word_1 = partial(decode_word, 1)
decode_word_1.decode_len = 2

decode_word_10 = partial(decode_word, 10)
decode_word_10.decode_len = 2


class CommandDecoder(namedtuple('CommandDecoder', 'start_position decode_fn number label')):
    """ Define a decoder for one of the registers in the response to a specific command. """

    def __hash__(self):
        """ Make hashable to allow them to be stored in sets. """
        return self.number

    @property
    def end_position(self):
        """ Return the end position, computed from the start position and decoder's decode_len. """
        return self.start_position + self.decode_fn.decode_len


prefix_to_decoders = {
    (3, 64, 0): [
        # 2020/06/01 22:51:45:
        # 19:O/U MPU ID (xx): 4 => 0;
        # 20:O/U MPU ID (yy): 57 => 0;
        # 21:O/U capacity (kW): 6 => 0;
        # Assuming these:
        # 43048,43058 22:51:45.0380990 [(3, 4, 0), (14, 57, 0), (15, 60, 0)]
        # [[3, 64, 0, 188], [64, 0, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 176]]
        # 44876,44887 22:52:00.0375973 [(15, 0, 60), (16, 176, 116)]
        # [[3, 64, 0, 188], [64, 0, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 60, 116]]
        # 46692,46703 22:52:15.0381757 [(13, 0, 4), (14, 0, 57), (16, 104, 43)]
        # [[3, 64, 0, 188], [64, 0, 15, 4, 1, 0, 1, 1, 1, 0, 2, 1, 1, 4, 57, 60, 43]]
        CommandDecoder(3, decode_byte_1, 19, "O/U MPU ID (xx)"),
        CommandDecoder(14, decode_byte_1, 20, "O/U MPU ID (yy)"),
        CommandDecoder(15, decode_byte_10, 21, "O/U capacity (kW)"),
    ],
    (3, 64, 16): [
        # 2020/06/01 22:49:35: 22:Operation Mode: Fan Only => Heating.
        # 2020/06/01 22:51:35: 22:Operation Mode: Heating => Fan Only.
        # Assuming this one:
        # 27304,27315 22:49:35.0694571 [(3, 0, 1)]
        # 41294,41305 22:51:30.0844895 [(3, 1, 0)]
        CommandDecoder(3, decode_bits[0], 22, "Operation Mode (Heating)"),
    ],
    (3, 64, 17): [
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
        CommandDecoder(3, decode_byte_1, 47, "O/U EEPROM (1st digit)"),
        CommandDecoder(4, decode_byte_1, 48, "O/U EEPROM (3rd 4th digit)"),
        CommandDecoder(5, decode_byte_1, 49, "O/U EEPROM (5th 6th digit)"),
        CommandDecoder(6, decode_byte_1, 50, "O/U EEPROM (7th 8th digit)"),
        CommandDecoder(7, decode_byte_1, 51, "O/U EEPROM (10th digit)"),
        CommandDecoder(8, decode_byte_1, 52, "O/U EEPROM (11th digit)"),
    ],
    (3, 64, 32): [
        # 2020/06/01 22:51:45: 33:Target Evap. Temp.(C): 32.6 => 0
        # 2020/06/01 22:52:15: 33:Target Evap. Temp.(C): 0 => 32.6
        # Assuming these:
        # 43204,43215 22:51:45.1785851 [(7, 74, 0), (8, 1, 0)]
        # 46240,46251 22:52:10.1786246 [(7, 0, 69), (8, 0, 1)]
        # TODO: double check this one. The numbers before and after the zero period, according
        # to the CSV export (32.6'C), are slightly different to the results from this decoder
        # (33.0'C and 32.5'C respectively).
        # CommandDecoder(7, decode_word_10, 56, "Target Evap. Temp.(C)"),
        # Actually, this appears to be incorrect, since the observed values match variable 56
        # exactly, so we still haven't found variable 33.
        # 2020/06/01 22:51:35: 54:Outdoor air temp.(R1T)(C): 16.5 => 16.0
        # Assumed to be:
        # 41992,42003 22:51:35.1785402 [(3, 165, 160), (20, 202, 207)]
        # [[3, 64, 32, 156], [64, 32, 19, 160, 0, 0, 0, 74, 1, 0, 0, 150, 0, 0, 0, 200, 0, 115, 0, 1, 207]]
        CommandDecoder(3, decode_word_10, 54, "Outdoor air temp.(R1T)(C)"),
        CommandDecoder(7, decode_word_10, 56, "Discharge pipe temp.(C)"),
        # 2020/06/01 22:51:05: 61:Pressure(kgcm2): 11.5 => 11.7
        # Assumed to be:
        # 37764,37775 22:51:00.1786083 [(11, 155, 150), (17, 115, 117), (20, 197, 200)]
        # [[3, 64, 32, 156], [64, 32, 19, 165, 0, 0, 0, 74, 1, 0, 0, 150, 0, 0, 0, 200, 0, 117, 0, 1, 200]]
        CommandDecoder(11, decode_word_10, 58, "Heat exchanger mid-temp.(C)"),
        CommandDecoder(17, decode_word_10, 61, "Pressure(kgcm2)"),
    ],
    (3, 64, 33): [
        # 2020/06/01 22:51:45: 63:INV primary current (A): 0.5 => 0
        # Assumed to be:
        # 43272,43283 22:51:45.2409813 [(3, 5, 0), (7, 243, 0), (10, 150, 0), (19, 254, 140)]
        # [[3, 64, 33, 155], [64, 33, 18, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 140]]
        CommandDecoder(3, decode_word_10, 63, "INV primary current (A)"),

        # 1252,1263 22:46:00.2408396 [(7, 61, 39)] (61 => 39)
        CommandDecoder(7, decode_byte_1, 65, "Voltage (N-phase) (V)"),
        # 2020/06/01 22:48:35: 58:Heat exchanger mid-temp.(C): 16 => 15.5'C
        # 2020/06/01 22:51:05: 58:Heat exchanger mid-temp.(C): 15.5 => 15'C
        # Assumed to be (seems very likely):
        # 21402,21413 22:48:45.2095790 [(10, 160, 155), (19, 193, 198)]
        # [[3, 64, 33, 155], [64, 33, 18, 5, 0, 0, 0, 38, 0, 0, 155, 0, 0, 0, 0, 0, 0, 0, 0, 198]]
        # 37832,37843 22:51:00.2409211 [(10, 155, 150), (19, 244, 249)]
        # [[3, 64, 33, 155], [64, 33, 18, 5, 0, 0, 0, 248, 0, 0, 150, 0, 0, 0, 0, 0, 0, 0, 0, 249]]
        # This value also appears to be in response 32 word at 11. There's currently no way to
        # distinguish between them, and we don't allow duplicates, so I'm commenting out this one.
        # CommandDecoder(10, decode_word_10, 58, "Heat exchanger mid-temp.(C)"),
    ],
    (3, 64, 48): [
        # 2020/06/01 22:51:45: 89:Expansion valve (pls): 450 => 0
        # Assumed to be:
        # 43330,43341 22:51:45.2880632 [(6, 194, 0), (7, 1, 0), (14, 191, 130)]
        # [[3, 64, 48, 140], [64, 48, 13, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 130]]
        CommandDecoder(6, decode_word_1, 89, "Expansion valve (pls)"),

        # 2020/06/01 22:49:45: 94:4 Way Valve 1: 0 => 1
        # 2020/06/01 22:51:45: 94:4 Way Valve 1: 1 => 0
        # Assumed to be:
        # 28136,28147 22:49:40.2879867 [(10, 0, 128), (14, 191, 63)]
        # [[3, 64, 48, 140], [64, 48, 13, 0, 0, 0, 194, 1, 0, 0, 128, 0, 0, 0, 63]]
        # 42720,42731 22:51:40.2882745 [(10, 128, 0), (14, 63, 191)]
        # [[3, 64, 48, 140], [64, 48, 13, 0, 0, 0, 194, 1, 0, 0, 0, 0, 0, 0, 191]]
        CommandDecoder(10, decode_bits[7], 94, "4 Way Valve 1"),
    ],
    (3, 64, 96): [
        CommandDecoder(15, decode_bits[5], 132, "BSH"),  # Booster heater ON/OFF?
    ],
    (3, 64, 97): [
        # 15000,15011 22:47:50.3817713 [(5, 116, 115)] (37.2 => 37.1)
        CommandDecoder(5, decode_word_10, 144, "Leaving water temp. before BUH (R1T)(C)"),
        # 4008,4019 22:46:21.4443689 [(7, 112, 111)] (36.8 => 36.7)
        CommandDecoder(7, decode_word_10, 145, "Leaving water temp. after BUH (R2T)(C)"),
        # 5208,5219 22:46:30.3658750 [(9, 37, 36)] (29.3 => 29.2)
        CommandDecoder(9, decode_word_10, 146, "Refrig. Temp. liquid side (R3T)(C)"),
        # 4008,4019 22:46:21.4443689 [(11, 68, 67)] (32.3 => 32.2)
        CommandDecoder(11, decode_word_10, 147, "Inlet water temp.(R4T)(C)"),
        # 5824,5835 22:46:35.4132092 [(13, 18, 20)] (53.0 => 53.2)
        CommandDecoder(13, decode_word_10, 148, "DHW tank temp. (R5T)(C)"),
        # 43446,43457 22:51:45.3971308 [(15, 250, 4)] (25.0 => 0.4)
        CommandDecoder(15, decode_word_10, 149, "Indoor ambient temp. (R1T)(C)"),
    ],
    (3, 64, 98): [
        # 5882,5893 22:46:35.4596000 [(5, 128, 144)] (bit 4 OFF => ON)
        CommandDecoder(5, decode_bits[4], 156, "Powerful DHW Operation. ON/OFF"),

        # 2020/06/01 22:51:45: 153:Reheat ON/OFF: 1 => 0
        # 2020/06/01 22:52:35: 153:Reheat ON/OFF: 0 => 0
        # Assumed to be:
        # 43514,43525 22:51:45.4443617 [(5, 144, 0)]
        # [[3, 64, 98, 90], [64, 98, 19, 128, 0, 0, 131, 1, 210, 0, 0, 0, 253, 255, 0, 100, 0, 0, 0, 0, 20]]
        # 49574,49585 22:52:35.4444182 [(5, 0, 128)]
        # [3, 64, 98, 90], [64, 98, 19, 128, 0, 128, 94, 1, 210, 0, 0, 1, 253, 255, 0, 100, 0, 0, 0, 0, 184]]
        CommandDecoder(5, decode_bits[7], 153, "Reheat ON/OFF"),

        # 2020/06/01 22:51:45: 161:LW setpoint (add)(C): 35 => 36.7 ([1, 94] => [1, 131])
        # 43514,43525 22:51:45.4443617 [(6, 94, 131)]
        CommandDecoder(6, decode_word_10, 161, "LW setpoint (add)(C)"),

        # 162:RT setpoint(C): 21 (210): assumed:
        CommandDecoder(8, decode_word_10, 162, "RT setpoint(C)"),

        # 25864,25875 22:49:20.4284707 [(10, 0, 16)] (bit 4 OFF => ON)
        # (assumed, could also be # 26346,26357 22:49:25.3190391 [(15, 0, 2)])
        CommandDecoder(10, decode_bits[4], 166, "Main RT Heating"),

        # 43514,43525 22:51:45.4443617 [(11, 1, 0)]
        # 44124,44135 22:51:50.4442968 [(11, 0, 1)]
        CommandDecoder(11, decode_bits[0], 178, "Space H Operation output"),

        # 27710,27721 22:49:35.4283079 [(12, 72, 118)]
        CommandDecoder(12, decode_word_10, 179, "Flow sensor (l/min)"),

        # 25864,25875 22:49:20.4284707 [(15, 100, 94)] (100 => 94)
        CommandDecoder(15, decode_byte_1, 181, "Water pump signal (0:max-100:stop)"),
    ],

    (3, 64, 99): [
        # 798,809 22:45:29.6316392
        # Assumed to be 194:Indoor Unit Address and 195-200:I/U EEPROM (BCD digits)
        # [[3, 64, 99, 89], [64, 99, 10, 128, 0, 1, 112, 100, 50, 21, 1, 181]]
        CommandDecoder(4, decode_byte_1, 194, "Indoor Unit Address"),
        CommandDecoder(5, decode_byte_1, 195, "I/U EEPROM (3rd digit)"),
        CommandDecoder(6, decode_byte_1, 196, "I/U EEPROM (4th 5th digit)"),
        CommandDecoder(7, decode_byte_1, 197, "I/U EEPROM (6th 7th digit)"),
        CommandDecoder(8, decode_byte_1, 198, "I/U EEPROM (8th 9th digit)"),
        CommandDecoder(9, decode_byte_1, 199, "I/U EEPROM (11th digit)"),
        CommandDecoder(10, decode_byte_1, 200, "I/U EEPROM (12th digit)(rev.)"),
    ],
}


def decode(command, response):
    """ Decode the response to a command. Returns a dictionary of "variable number" to value. """
    values = {}

    for prefix, decoders in prefix_to_decoders.items():
        if tuple(command[:len(prefix)]) == prefix:
            for decoder in decoders:
                response_part = response[decoder.start_position:decoder.end_position]
                value = decoder.decode_fn(response_part)
                values[decoder.number] = (decoder, value)

    return values
