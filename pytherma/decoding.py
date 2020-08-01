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
    (3, 64, 33): [
        # 1252,1263 22:46:00.2408396 [(7, 61, 39)] (61 => 39)
        CommandDecoder(7, decode_byte_1, 65, "Voltage (N-phase) (V)"),
    ],
    (3, 64, 16): [
        # 2020/06/01 22:49:35: 22:Operation Mode: Fan Only => Heating.
        # 2020/06/01 22:51:35: 22:Operation Mode: Heating => Fan Only.
        # Assuming this one:
        # 27304,27315 22:49:35.0694571 [(3, 0, 1)]
        # 41294,41305 22:51:30.0844895 [(3, 1, 0)]
        CommandDecoder(3, decode_bits[0], 22, "Operation Mode (Heating)"),
    ],
    (3, 64, 48): [
        # 2020/06/01 22:51:45: 153:Reheat ON/OFF ON => OFF. Assuming this one (byte 10 bit 7):
        # 42720,42731 22:51:40.2882745 [(10, 128, 0)]
        CommandDecoder(10, decode_bits[7], 153, "Reheat ON/OFF"),
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
