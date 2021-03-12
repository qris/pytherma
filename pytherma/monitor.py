""" Poll the Daikin ASHP and record its state in the database. """

import argparse
import logging
import re
import serial
import sqlalchemy

from pytherma.sql import Base
from pytherma.decoding import decode_p1p2


def parse_read_bytes(read_bytes_hex, engine):
    """ Parse an R: (raw bytes read) line from P1P2Serial. """
    decoded = read_bytes_hex.decode('ascii')
    buf = bytearray.fromhex(decoded)
    print(decoded, decode_p1p2(buf))


def parse_line(line, engine):
    """ Parse an individual output line from the P1P2Monitor Arduino program.

    Record the useful decoded values in the database.
    """
    match = re.match(b'R ([0-9.]+): ([0-9A-F]+) CRC=([0-9A-F]+)', line)
    if match is not None:
        parse_read_bytes(match.group(2), match.group(3))
    elif line.startswith(b'J '):
        # Ignore JSON lines for now
        return
    else:
        logging.info("Ignoring unknown message type: {line}")

    # with session_scope(engine) as session:


def main_loop(serial_port, engine):
    """ Monitor the Daikin P1/P2 bus indefinitely, recording ASHP state in the database. """
    while True:
        line = serial_port.readline()
        parse_line(line, engine)


def main(cmdline_args=None):
    """ Run the P1/P2 monitor as a command-line application. """
    parser = argparse.ArgumentParser(description=("Monitor the Daikin P1/P2 bus and record ASHP state in the database."))
    parser.add_argument('--port', required=True,
                        help="Serial port (device) connected to Arduino with P1P2Serial adaptor")
    parser.add_argument('--speed', required=False, default=115200,
                        help="Baud rate for serial port (device) connected to Arduino with P1P2Serial adaptor")
    parser.add_argument('--database', required=True,
                        help="SQLAlchemy URL for the database to connect to")
    parser.add_argument('--create', action='store_true',
                        help="Create database tables if missing")

    args = parser.parse_args(cmdline_args)

    serial_port = serial.Serial(args.port, args.speed)

    # 'postgresql+psycopg2://<username>:<password>@localhost/<database>'
    engine = sqlalchemy.create_engine(args.database)
    if args.create:
        Base.metadata.create_all(engine)

    main_loop(serial_port, engine)
