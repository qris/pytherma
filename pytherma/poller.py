""" Poll the Daikin ASHP and record its state in the database. """

import argparse
import datetime
import sqlalchemy
import sys
import time

from enum import Enum

import serial

import pytherma
import pytherma.comms
import pytherma.simulator

from pytherma import decoding
from pytherma.sql import Base, SerialState, session_scope
from pytherma.espaltherma import parse_espaltherma_definition


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
    if False:
        daikin_interface.write(b'$$$')
        try:
            response = daikin_interface.read(2)
        except TimeoutError:
            # Try once more
            daikin_interface.write(b'$$$')
            response = daikin_interface.read(2)

        assert response == b'\x15\xea', f"Unexpected response from Daikin unit: {response}"

        daikin_interface.write(bytes.fromhex('02 4E AF 30 30 30 30 BD 03'))
        response = daikin_interface.read(2)
        assert response == b'\xfe', f"Unexpected response from Daikin unit: {response}"

    while True:
        time.sleep(poll_interval)
        poll_once(daikin_interface, decoding_table, engine)


class TimeoutError(Exception):
    """ Raised when the Daikin does not reply to a command in time. """


class SerialDevice:
    """ Wraps a serial.Serial with a slightly nicer API, also the same as that of DaikinSimulator. """

    def __init__(self, device, verbose):
        self.device = device
        self.verbose = verbose

    def write(self, command):
        """ Write a  command. """
        assert isinstance(command, bytes)
        if self.verbose:
            if sys.version_info >= (3, 8):
                print(f"{datetime.datetime.now().time()} D<-C {command.hex(' ')}")
            else:
                hex_str = ' '.join(bytes([b]).hex() for b in command)
                print(f"{datetime.datetime.now().time()} D<-C {hex_str}")
        self.device.write(command)

    def can_read(self):
        """ Return whether (or not) there is data in the response buffer, waiting to be read. """
        return self.device.in_waiting > 0

    def read(self, length=1):
        """ Read some bytes from the device.

        This will block for 1 second, which should be way longer than we expect to wait for a reply, and then raise
        a TimeoutError.
        """
        self.device.timeout = 1
        response = self.device.read(length)
        if len(response) < length:
            raise TimeoutError("Timed out waiting for a response from the Daikin")
        if self.verbose:
            if sys.version_info >= (3, 8):
                print(f"{datetime.datetime.now().time()} D->C {response.hex(' ')}")
            else:
                hex_str = ' '.join(bytes([b]).hex() for b in response)
                print(f"{datetime.datetime.now().time()} D->C {hex_str}")
        return response


def main(cmdline_args=None):
    """ Run the poller as a command-line application. Called by bin/poller.py. """
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
    parser.add_argument('--port',
                        help="Serial port (device) connected to D-Checker serial adaptor")
    parser.add_argument('--speed', required=False, default=9600,
                        help="Baud rate for serial port (device) connected to D-Checker serial adaptor")
    parser.add_argument('--debug', action='store_true',
                        help="Print packets sent and received")

    args = parser.parse_args(cmdline_args)

    if args.definitions_file is not None:
        with open(args.definitions_file) as f:
            definitions_text = f.read()
        decoding_table = parse_espaltherma_definition(definitions_text, output_text=False)
    else:
        decoding_table = decoding.serial_page_prefix_to_decoders

    # 'postgresql+psycopg2://<username>:<password>@localhost/<database>'
    engine = sqlalchemy.create_engine(args.database)
    if args.create:
        Base.metadata.create_all(engine)

    assert bool(args.port) ^ args.simulator, "You must use either --port or --simulator, but not both"

    if args.simulator:
        daikin_interface = pytherma.simulator.DaikinSimulator()
    else:
        raw_serial = serial.Serial(args.port, args.speed, parity=serial.PARITY_EVEN)
        daikin_interface = SerialDevice(raw_serial, args.debug)

    main_loop(daikin_interface, decoding_table, engine, args.interval)
