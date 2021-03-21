""" Convert ESPAltherma definition files to our CommandDecoder structures. """

import re

from pytherma import decoding


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
                # little endian byte or word -> unsigned int
                converter = None  # not supported yet
            elif convid == 152:
                # big endian byte or word -> unsigned int
                converter = None  # not supported yet
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
                converter = 'decode_byte_1'  # just return a number for now
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
                converter = None  # not supported yet
            elif convid >= 300 and convid <= 307:
                # bit -> boolean, 300 = bit 0, 307 = bit 7
                assert length == 1
                converter = f"decode_bits[{convid - 300}]"
            elif convid == 315:
                # byte -> ["Stop","Heating","Cooling","??","DHW:Domestic Hot Water"...][i >> 4]
                assert length == 1
                converter = None  # not supported yet
            elif convid == 316:
                # byte -> ["H/P only","Hybrid","Boiler only"][i >> 4]
                assert length == 1
                converter = None  # not supported yet
            else:
                raise ValueError(f"Unsupported conversion {convid} in {line!r}")

            if converter is None:
                continue

            espaltherma_offset = offset - 3

            # The ESPaltherma files don't tell us what ID is assigned to the variable in D-Checker,
            # but we need some kind of unique identifier, so make one up:
            synthetic_id = f"{registry_id}.{espaltherma_offset}.{convid}"

            if output_text:
                if not isinstance(converter, str):
                    converter = converter.__name__
                decoders.append(f'CommandDecoder({offset}, {converter}, {synthetic_id!r}, {label!r})')
            else:
                if isinstance(converter, str):
                    converter = eval(converter, vars(decoding))
                decoders.append(decoding.CommandDecoder(offset, converter, synthetic_id, label))

    return prefix_to_decoders
