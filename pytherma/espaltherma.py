""" Convert ESPAltherma definition files to our CommandDecoder structures. """

import os
import re

from enum import Enum
from pytherma import decoding

DEFINITION_FILES = os.path.join(os.path.dirname(__file__), '..', 'data')


class OperationMode(Enum):
    """ Possible values for Operation Mode variable. """

    fan_only = "Fan Only"
    heating = "Heating"
    cooling = "Cooling"
    auto = "Auto"
    ventilation = "Ventilation"
    auto_cool = "Auto Cool"
    auto_heat = "Auto Heat"
    dry = "Dry"
    aux = "Aux."
    cooling_storage = "Cooling Storage"
    heating_storage = "Heating Storage"
    use_stored_cool_1 = "UseStrdThrm(cl)1"
    use_stored_cool_2 = "UseStrdThrm(cl)2"
    use_stored_cool_3 = "UseStrdThrm(cl)3"
    use_stored_cool_4 = "UseStrdThrm(cl)4"
    use_stored_heat_1 = "UseStrdThrm(ht)1"
    use_stored_heat_2 = "UseStrdThrm(ht)2"
    use_stored_heat_3 = "UseStrdThrm(ht)3"
    use_stored_heat_4 = "UseStrdThrm(ht)4"

    @classmethod
    def value_lookup_table(cls):
        """ Return the possible values, in integer lookup order. """
        return [cls.fan_only, cls.heating, cls.cooling, cls.auto, cls.ventilation, cls.auto_cool,
                cls.auto_heat, cls.dry, cls.aux, cls.cooling_storage, cls.heating_storage,
                cls.use_stored_cool_1, cls.use_stored_cool_2, cls.use_stored_cool_3,
                cls.use_stored_cool_4, cls.use_stored_heat_1, cls.use_stored_heat_2,
                cls.use_stored_heat_3, cls.use_stored_heat_4]

    @classmethod
    def from_int(cls, value):
        """ Return the enum instance corresponding to the supplied value, which must be an integer. """
        return cls.value_lookup_table()[int(value)]

    def to_int(self):
        """ Return the integer corresponding to this instance. """
        return self.value_lookup_table().index(self)


class IUOperationMode(Enum):
    """ Possible values for I/U Operation Mode variable. """

    stop = "Stop"
    heating = "Heating"
    cooling = "Cooling"
    unknown = "??"
    dhw = "DHW"
    heating_dhw = "Heating + DHW"
    cooling_dhw = "Cooling + DHW"

    @classmethod
    def value_lookup_table(cls):
        """ Return the possible values, in integer lookup order. """
        return [cls.stop, cls.heating, cls.cooling, cls.unknown, cls.dhw, cls.heating_dhw,
                cls.cooling_dhw]

    @classmethod
    def from_int(cls, value):
        """ Return the enum instance corresponding to the supplied value, which must be an integer. """
        return cls.value_lookup_table()[int(value) >> 4]

    def to_int(self):
        """ Return the integer corresponding to this instance. """
        return self.value_lookup_table().index(self) << 4


def _processed_value(name, raw_decoder, post_processor):
    def processor(data_bytes):
        raw_value = raw_decoder(data_bytes)
        return post_processor(raw_value)
    processor.__name__ = name
    processor.decode_len = raw_decoder.decode_len
    return processor


decode_operation_mode = _processed_value('decode_operation_mode', decoding.decode_byte_1, OperationMode.from_int)
decode_iu_operation_mode = _processed_value('decode_iu_operation_mode', decoding.decode_byte_1, IUOperationMode.from_int)
decode_211 = _processed_value('decode_211', decoding.decode_byte_1, lambda value: None if value == 0 else value)


def parse_espaltherma_definition(definition_text, output_text):
    """ Return a CommandDecoder structure built from the supplied definitions.

    If output_text is True, definitions will be output as source code, to generate Python
    script files. If False, actual CommandDecoder instances will be returned instead, for
    on-the-fly decoder table generation.
    """
    prefix_to_decoders = {}

    for line in definition_text.splitlines():
        match = re.match(r'//{(?P<registryID>0x?[0-9A-Fa-f]{2}),(?P<offset>\d+),(?P<convid>\d+),'
                         r'(?P<dataSize>\d+),(?P<dataType>-?\d+),"(?P<label>[^"]*)"},', line)
        if match is not None:
            registry_id = int(match.group('registryID'), 16)

            prefix = (3, 64, registry_id)
            if prefix in prefix_to_decoders:
                decoders = prefix_to_decoders[prefix]
            else:
                prefix_to_decoders[prefix] = decoders = []

            # We include the response sender address byte, page number and length (3 bytes) in the
            # response for purposes of offset calculation, but ESPAltherma does not, so we need to
            # add 3 to their offset to get ours:
            offset = int(match.group('offset')) + 3
            convid = int(match.group('convid'))
            length = int(match.group('dataSize'))
            label  = match.group('label')

            # Convert convid to a Python converter function:
            # https://github.com/raomin/ESPAltherma/blob/main/include/converters.h
            if convid == 100:
                # text
                converter = None  # not supported yet
            elif convid == 101:
                # byte or little endian word -> signed integer
                converter = 'decode_byte_1' if length == 1 else 'decode_word_1'
            elif convid == 102:
                # byte or big endian word -> signed integer
                converter = None  # not supported yet
            elif convid == 103:
                # little endian word -> signed float with 8 bits decimal
                assert length == 2
                converter = None  # not supported yet
            elif convid == 104:
                # big endian word -> signed float with 8 bits decimal (i.e. /256)
                assert length == 2
                converter = '.decode_word_fixed_prec_be'
            elif convid == 105:
                # byte or little endian word -> signed float with one digit decimal (i.e. /10)
                converter = 'decode_byte_10' if length == 1 else 'decode_word_10'
            elif convid == 106:
                # byte or big endian word -> signed float with one digit decimal (i.e. /10)
                converter = None  # not supported yet
            elif convid == 107:
                # little endian word -> signed float with one digit decimal (i.e. /10) and 0x8000 -> N/A
                assert length == 2
                converter = None  # not supported yet
            elif convid == 108:
                # big endian word -> signed float with one digit decimal (i.e. /10) and 0x8000 -> N/A
                assert length == 2
                converter = None  # not supported yet
            elif convid == 109:
                # little endian word -> signed float with 7 bits decimal (i.e. /128)
                assert length == 2
                converter = None  # not supported yet
            elif convid == 110:
                # big endian word -> signed float with 7 bits decimal (i.e. /128)
                assert length == 2
                converter = None  # not supported yet
            elif convid == 111:
                # big endian word -> signed float with 1 bit decimal (i.e. /2)
                assert length == 2
                converter = None  # not supported yet
            elif convid == 112:
                # big endian word -> signed float with 1 bit decimal (i.e. /2) and offset by +64
                assert length == 2
                converter = None  # not supported yet
            elif convid == 113:
                # big endian word -> signed float with 2 bits decimal (i.e. /4)
                assert length == 2
                converter = None  # not supported yet
            elif convid == 114:
                # little endian word -> signed float with 8 bits decimal (i.e. /256) and 0x8000 (LE) -> N/A
                assert length == 2
                converter = None  # not supported yet
            elif convid == 115:
                # little endian word -> signed float with scale 2560 (i.e. /256 and then /10!)
                assert length == 2
                converter = None  # not supported yet
            elif convid == 116:
                # big endian word -> signed float with scale 2560 (i.e. /256 and then /10!)
                assert length == 2
                converter = None  # not supported yet
            elif convid == 117:
                # little endian word -> signed float with scale 100 (i.e. /100)
                assert length == 2
                converter = None  # not supported yet
            elif convid == 118:
                # big endian word -> signed float with scale 100 (i.e. /100)
                assert length == 2
                converter = None  # not supported yet
            elif convid == 118:
                # little endian word -> unsigned float with 8 bits decimal (i.e. /256) and 0x8000 (LE) -> N/A
                assert length == 2
                converter = None  # not supported yet
            elif convid == 151:
                # byte or little endian word -> unsigned int
                converter = 'decode_byte_1' if length == 1 else 'decode_word_1'
            elif convid == 152:
                # byte or big endian word -> unsigned int
                assert length in (1, 2)
                converter = 'decode_byte_1' if length == 1 else 'decode_word_1_be'
            elif convid == 153:
                # little endian word -> unsigned float with 8 bits decimal (i.e. /256)
                converter = None  # not supported yet
            elif convid == 154:
                # big endian word -> unsigned float with 8 bits decimal (i.e. /256)
                converter = None  # not supported yet
            elif convid == 155:
                # little endian word -> unsigned float with one digit decimal (i.e. /10)
                assert length == 2
                converter = None  # not supported yet
            elif convid == 156:
                # big endian word -> unsigned float with one digit decimal (i.e. /10)
                assert length == 2
                converter = None  # not supported yet
            elif convid == 157:
                # little endian word -> unsigned float with scale 128 (7 bits decimal)
                assert length == 2
                converter = None  # not supported yet
            elif convid == 158:
                # big endian word -> unsigned float with scale 128 (7 bits decimal)
                assert length == 2
                converter = None  # not supported yet
            elif convid == 200:
                # byte -> OFF (zero) or ON (nonzero)
                assert length == 1
                converter = None  # not supported yet
            elif convid in (201, 217):
                # byte -> ["Fan Only","Heating","Cooling",...][i]
                assert length == 1
                converter = decode_operation_mode
            elif convid == 203:
                # byte -> ["Normal", "Error", "Warning", "Caution"][i]
                assert length == 1
                converter = None  # not supported yet
            elif convid == 204:
                # byte -> hex, nibble swapped, weird transformation (ACEHFJLPU987654, 0123456789AHCJEF)
                assert length == 1
                converter = None  # not supported yet
            elif convid == 211:
                # byte -> integer where 0 = "OFF"
                assert length == 1
                converter = decode_211
            elif convid >= 300 and convid <= 307:
                # bit -> boolean, 300 = bit 0, 307 = bit 7
                assert length == 1
                converter = f"decode_bits[{convid - 300}]"
            elif convid == 315:
                # byte -> ["Stop","Heating","Cooling","??","DHW:Domestic Hot Water"...][i >> 4]
                assert length == 1
                converter = decode_iu_operation_mode
            elif convid == 316:
                # byte -> ["H/P only","Hybrid","Boiler only"][i >> 4]
                assert length == 1
                converter = None  # not supported yet
            elif convid in (214, 215, 219, 310, 311, 405, 801, 995, 996, 998):
                # unknown, not implemented in espaltherma
                converter = None  # not supported yet
            else:
                raise ValueError(f"Unsupported conversion {convid} in {line!r}")

            if converter is None:
                continue

            espaltherma_offset = offset - 3

            # The ESPaltherma files don't tell us what ID is assigned to the variable in D-Checker,
            # but we need some kind of unique identifier, so make one up:
            synthetic_id = f"{registry_id:02x}.{espaltherma_offset}.{convid}"

            if output_text:
                if not isinstance(converter, str):
                    converter = converter.__name__
                decoders.append(f'CommandDecoder({offset}, {converter}, {synthetic_id!r}, {label!r})')
            else:
                if isinstance(converter, str):
                    converter = eval(converter, vars(decoding))
                decoders.append(decoding.CommandDecoder(offset, converter, synthetic_id, label))

    return prefix_to_decoders
