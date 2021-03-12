""" Poll the Daikin ASHP and record its state in the database. """

import argparse
import datetime
import sqlalchemy
import time

import pytherma
import pytherma.comms
import pytherma.decoding
import pytherma.simulator

from pytherma.sql import Base, DaikinState, session_scope


def poll_once(daikin_interface, engine):
    """ Poll Daikin ASHP once for all known pages.

    Record their raw contents and decoded values in the database.
    """
    with session_scope(engine) as session:
        daikin_state = DaikinState(timestamp=datetime.datetime.now().astimezone(),
                                   raw_page_contents={}, variable_values={})
        session.add(daikin_state)

        for prefix in pytherma.decoding.serial_page_prefix_to_decoders:
            command_packet = bytes(prefix) + pytherma.comms.calculate_checksum(prefix)

            response_packet = pytherma.comms.execute_command(daikin_interface, command_packet)
            daikin_state.raw_page_contents[prefix[2]] = list(response_packet[3:-1])

            values = pytherma.decoding.decode_serial(command_packet, response_packet)
            # JSON dict keys are always strings, so for the avoidance of doubt, we convert
            # the keys to strings here. https://stackoverflow.com/questions/1450957
            daikin_state.variable_values.update({
                str(number): value[1] for number, value in values.items()
            })


def main_loop(daikin_interface, engine, poll_interval):
    """ Poll Daikin ASHP repeatedly at fixed intervals until stopped. """
    while True:
        time.sleep(poll_interval)
        poll_once(daikin_interface, engine)


def main(cmdline_args=None):
    """ Run the poller as a command-line application. """
    parser = argparse.ArgumentParser(description=("Poll a Daikin Altherma ASHP using serial "
                                                  "commands, and write to a database."))
    parser.add_argument('--database', required=True,
                        help="SQLAlchemy URL for the database to connect to")
    parser.add_argument('--create', action='store_true',
                        help="Create database tables if missing")
    parser.add_argument('--interval', type=int, default=5,
                        help=("Time in seconds between each polling of the Altherma "
                              "for updated values, and between database writes"))
    parser.add_argument('--simulator', action='store_true',
                        help="Read values from the simulator instead of a real Altherma unit")

    args = parser.parse_args(cmdline_args)

    # 'postgresql+psycopg2://<username>:<password>@localhost/<database>'
    engine = sqlalchemy.create_engine(args.database)
    if args.create:
        Base.metadata.create_all(engine)

    assert args.simulator, "Real comms are not supported yet, only the Simulator"
    daikin_interface = pytherma.simulator.DaikinSimulator()

    main_loop(daikin_interface, engine, args.interval)
