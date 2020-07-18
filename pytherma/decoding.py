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

    * The prefix of the command to whose response they apply (e.g. (3, 64, 33)).
    * The offset of the first byte to which the decoder applies (start_position). The length
      is determined by the decoder function (specifically its decode_len attribute).
      E.g. decode_word with an offset of 7 consumes bytes 7 and 8.
    * The decoder function, e.g. decode_byte_1. Must take a single argument, which will
      be passed the bytes from the offset to the offset plus decode_len of the function.
      For example, decode_word with an offset of 7 will be passed response[7:8].
      Therefore generic decoders (such as decode_byte) must be wrapped to supply the initial
      arguments (divisor), e.g. using partial or the canned shortcuts (decode_bits[4],
      decode_word_10, etc).
    * The corresponding "variable number" in D-Checker, displayed in the user interface and
      in the column heading of the CSV export (see contrib/1_20200601-224524.csv for
      examples).
    * The description of the variable, which may also be in the CSV header, possibly modified
      for readability (e.g. "Voltage (N-phase) (V)")

    Unsigned integers (especially words) are often scaled by 10 to accommodate fixed point
    real numbers, e.g. the value 273 means 27.3. The decode_word_10 shortcut handles this.
    No scaled byte values are known, so you probably want to use decode_byte_1.
"""

from collections import namedtuple
from functools import partial


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


def decode_word(divisor, data_bytes):
    """ Extract two bytes from the specified response byte, returns an integer. """
    if len(data_bytes) == 2:
        return ((data_bytes[1] * 256) + data_bytes[0]) / divisor
    else:
        return None


decode_word_10 = partial(decode_word, 10)
decode_word_10.decode_len = 2


class CommandDecoder(namedtuple('CommandDecoder', 'prefix start_position decode_fn number label')):
    """ Define a decoder for one of the registers in the response to the the specified command. """

    def __hash__(self):
        """ Make hashable to allow them to be stored in sets. """
        return self.number

    @property
    def end_position(self):
        """ Return the end position, computed from the start position and decoder's decode_len. """
        return self.start_position + self.decode_fn.decode_len


command_decoders = [
    # 1252,1263 22:46:00.2408396 [(7, 61, 39)] (61 => 39)
    CommandDecoder((3, 64, 33), 7, decode_byte_1, 65, "Voltage (N-phase) (V)"),
    # 15000,15011 22:47:50.3817713 [(5, 116, 115)] (37.2 => 37.1)
    CommandDecoder((3, 64, 97), 5, decode_word_10, 144, "Leaving water temp. before BUH (R1T)(C)"),
    # 4008,4019 22:46:21.4443689 [(7, 112, 111)] (36.8 => 36.7)
    CommandDecoder((3, 64, 97), 7, decode_word_10, 145, "Leaving water temp. after BUH (R2T)(C)"),
    # 5208,5219 22:46:30.3658750 [(9, 37, 36)] (29.3 => 29.2)
    CommandDecoder((3, 64, 97), 9, decode_word_10, 146, "Refrig. Temp. liquid side (R3T)(C)"),
    # 4008,4019 22:46:21.4443689 [(11, 68, 67)] (32.3 => 32.2)
    CommandDecoder((3, 64, 97), 11, decode_word_10, 147, "Inlet water temp.(R4T)(C)"),
    # 5824,5835 22:46:35.4132092 [(13, 18, 20)] (53.0 => 53.2)
    CommandDecoder((3, 64, 97), 13, decode_word_10, 148, "DHW tank temp. (R5T)(C)"),
    # 5882,5893 22:46:35.4596000 [(5, 128, 144)] (bit 4 OFF => ON)
    CommandDecoder((3, 64, 98), 5, decode_bits[4], 156, "Powerful DHW Operation. ON/OFF"),
    # 25864,25875 22:49:20.4284707 [(10, 0, 16)] (bit 4 OFF => ON)
    # (assumed, could also be # 26346,26357 22:49:25.3190391 [(15, 0, 2)])
    CommandDecoder((3, 64, 98), 10, decode_bits[4], 166, "Main RT Heating"),
    # 25864,25875 22:49:20.4284707 [(15, 100, 94)] (100 => 94)
    CommandDecoder((3, 64, 98), 15, decode_byte_1, 181, "Water pump signal (0:max-100:stop)"),
]


def decode(command, response):
    """ Decode the response to a command. Returns a dictionary of "variable number" to value. """
    values = {}

    for decoder in command_decoders:
        if decoder.prefix == tuple(command[:len(decoder.prefix)]):
            response_part = response[decoder.start_position:decoder.end_position]
            value = decoder.decode_fn(response_part)
            values[decoder.number] = (decoder, value)

    return values
