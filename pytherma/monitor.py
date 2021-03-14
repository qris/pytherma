""" Poll the Daikin ASHP and record its state in the database. """

import argparse
import datetime
import logging
import re
import serial
import sqlalchemy

from pytherma.sql import Base, P1P2State, session_scope
from pytherma.decoding import decode_p1p2


class DatabaseOutputPlugin:
    """ An output plugin that writes to a SQL database using SQLAlchemy. """

    def __init__(self, database_url):
        # 'postgresql+psycopg2://<username>:<password>@localhost/<database>'
        self.engine = sqlalchemy.create_engine(database_url)
        self.record = None

    def initialise(self):
        """ Initialise the plugin when run for the first time, i.e. create database tables. """
        Base.metadata.create_all(self.engine)

    def handle_parsed_values(self, values):
        """ Handle some values parsed by decode_p1p2, by collecting them ready to write to the database. """
        if self.record is None:
            self.record = P1P2State(timestamp=datetime.datetime.now().astimezone())
        for name, (decoder, value) in values.items():
            setattr(self.record, name.value, value)

    def round_finished(self):
        """ Write values collected so far to the database, and clear them. """
        if self.record is not None:
            with session_scope(self.engine) as session:
                session.add(self.record)
            self.record = None


def parse_read_bytes(read_bytes_hex, engine):
    """ Parse an R: (raw bytes read) line from P1P2Serial. """
    decoded = read_bytes_hex.decode('ascii')
    buf = bytearray.fromhex(decoded)
    parsed_values = decode_p1p2(buf)
    print(decoded, parsed_values)
    return parsed_values


def parse_line(line, output_plugins):
    """ Parse an individual output line from the P1P2Monitor Arduino program.

    Record the useful decoded values in the database.
    """
    if line.startswith(b'R '):
        match = re.match(b'R ([0-9.]+): ([0-9A-F]+) CRC=([0-9A-F]+)', line)
        assert match is not None, f"Failed to match raw read line: {line!r}"
        if match.group(2).startswith(b'4000100'):
            # A bit ugly: if we see this packet, assume that we have finished the previous round of
            # polling.
            for plugin in output_plugins:
                plugin.round_finished()

        result = parse_read_bytes(match.group(2), match.group(3))
        for plugin in output_plugins:
            plugin.handle_parsed_values(result)
    elif line.startswith(b'J '):
        # Ignore JSON lines for now
        return
    else:
        logging.info("Ignoring unknown message type: {line}")

    # with session_scope(engine) as session:


def main_loop(serial_port, output_plugins):
    """ Monitor the Daikin P1/P2 bus indefinitely, recording ASHP state in the database. """
    while True:
        line = serial_port.readline()
        parse_line(line, output_plugins)


def main(cmdline_args=None):
    """ Run the P1/P2 monitor as a command-line application. """
    parser = argparse.ArgumentParser(description=("Monitor the Daikin P1/P2 bus and record ASHP state in the database."))
    parser.add_argument('--port', required=True,
                        help="Serial port (device) connected to Arduino with P1P2Serial adaptor")
    parser.add_argument('--speed', required=False, default=115200,
                        help="Baud rate for serial port (device) connected to Arduino with P1P2Serial adaptor")
    parser.add_argument('--database',
                        help="SQLAlchemy URL for the database to connect to")
    parser.add_argument('--init', action='store_true',
                        help="Initialise plugins (e.g. create database tables if missing)")

    args = parser.parse_args(cmdline_args)

    serial_port = serial.Serial(args.port, args.speed)

    output_plugins = []
    if args.database:
        output_plugins.append(DatabaseOutputPlugin(args.database))

    if args.init:
        for plugin in output_plugins:
            plugin.initialise()

    main_loop(serial_port, output_plugins)
