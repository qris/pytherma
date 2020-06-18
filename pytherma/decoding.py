from collections import namedtuple
from functools import partial

def decode_bit(bit, data_bytes):
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
    if len(data_bytes) == 1:
        return data_bytes[0] / divisor
    else:
        return None

decode_byte_1 = partial(decode_byte, 1)
decode_byte_1.decode_len = 1

def decode_word(divisor, data_bytes):
    if len(data_bytes) == 2:
        return ((data_bytes[1] * 256) + data_bytes[0]) / divisor
    else:
        return None

decode_word_10 = partial(decode_word, 10)
decode_word_10.decode_len = 2

class CommandDecoder(namedtuple('CommandDecoder', 'prefix start_position decode_fn number label')):
    def __hash__(self):
        return self.number

    @property
    def end_position(self):
        return self.start_position + self.decode_fn.decode_len

command_decoders = [
    # 1252,1263 22:46:00.2408396 [(7, 61, 39)] (61 => 39)
    CommandDecoder((3, 64, 33), 7, decode_byte_1, 65, "Voltage (N-phase) (V)"),
    # 25864,25875 22:49:20.4284707 [(10, 0, 16)] (bit 4 OFF => ON)
    # (assumed, could also be # 26346,26357 22:49:25.3190391 [(15, 0, 2)])
    CommandDecoder((3, 64, 98), 10, decode_bits[4], 166, "Main RT Heating"),
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
    # 25864,25875 22:49:20.4284707 [(15, 100, 94)] (100 => 94)
    CommandDecoder((3, 64, 98), 15, decode_byte_1, 181, "Water pump signal (0:max-100:stop)"),
]

def decode(command, response):
    values = {}

    for decoder in command_decoders:
        if decoder.prefix == tuple(command[:len(decoder.prefix)]):
            response_part = response[decoder.start_position:decoder.end_position]
            value = decoder.decode_fn(response_part)
            values[decoder.number] = (decoder, value)

    return values

