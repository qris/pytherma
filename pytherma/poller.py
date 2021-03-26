""" Poll the Daikin ASHP and record its state in the database. """

import argparse
import datetime
import sqlalchemy
import time

from enum import Enum

import pytherma
import pytherma.comms
import pytherma.simulator

from pytherma import decoding
from pytherma.sql import Base, SerialState, session_scope


def _adapt_value_to_json(value):
    """ Return a JSON-compatible representation of a decoded value. """
    if isinstance(value, Enum):
        return value.value
    else:
        return value


def poll_once(daikin_interface, decoding_table, engine):
    """ Poll Daikin ASHP once for all known pages.

    Record their raw contents and decoded values in the database.
    """
    with session_scope(engine) as session:
        serial_state = SerialState(timestamp=datetime.datetime.now().astimezone(),
                                   raw_page_contents={}, variable_values={})
        session.add(serial_state)

        for prefix in decoding_table:
            command_packet = bytes(prefix) + pytherma.comms.calculate_checksum(prefix)

            response_packet = pytherma.comms.execute_command(daikin_interface, command_packet)
            serial_state.raw_page_contents[prefix[2]] = list(response_packet[3:-1])

            values = decoding.decode_using_table(command_packet, response_packet, decoding_table)

            # JSON dict keys are always strings, so for the avoidance of doubt, we convert
            # the keys to strings here. https://stackoverflow.com/questions/1450957
            serial_state.variable_values.update({
                str(variable_id): _adapt_value_to_json(value[1]) for variable_id, value in values.items()
            })


def main_loop(daikin_interface, decoding_table, engine, poll_interval):
    """ Poll Daikin ASHP repeatedly at fixed intervals until stopped. """
    while True:
        time.sleep(poll_interval)
        poll_once(daikin_interface, decoding_table, engine)


def main(cmdline_args=None):
    """ Run the poller as a command-line application. """
    parser = argparse.ArgumentParser(description=("Poll a Daikin Altherma ASHP using serial "
                                                  "commands, and write to a database."))
    parser.add_argument('--database', required=True,
                        help="SQLAlchemy URL for the database to connect to")
    parser.add_argument('--definitions-file',
                        help="Path to ESPAltherma definitions file for your device (defaults to built-in EHBH/X)")
    parser.add_argument('--create', action='store_true',
                        help="Create database tables if missing")
    parser.add_argument('--interval', type=int, default=5,
                        help=("Time in seconds between each polling of the Altherma "
                              "for updated values, and between database writes"))
    parser.add_argument('--simulator', action='store_true',
                        help="Read values from the simulator instead of a real Altherma unit")

    args = parser.parse_args(cmdline_args)

    if args.definitions_file is not None:
        with open(args.definitions_file) as f:
            definitions_text = f.read()
        decoding_table = decoding.parse_espaltherma_definition(definitions_text, output_text=False)
    else:
        decoding_table = decoding.serial_page_prefix_to_decoders

    # 'postgresql+psycopg2://<username>:<password>@localhost/<database>'
    engine = sqlalchemy.create_engine(args.database)
    if args.create:
        Base.metadata.create_all(engine)

    assert args.simulator, "Real comms are not supported yet, only the Simulator"
    daikin_interface = pytherma.simulator.DaikinSimulator()

    main_loop(daikin_interface, decoding_table, engine, args.interval)
