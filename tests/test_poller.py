""" Tests for the poller module. """

import os
import sqlalchemy
import unittest

from pytherma import decoding, poller, sql
from pytherma.simulator import DaikinSimulator
from pytherma.espaltherma import DEFINITION_FILES, parse_espaltherma_definition


class PollerTest(unittest.TestCase):
    """ Tests for the poller module. """

    def test_poll_once(self):
        """ Test that poll_once() works as expected using built-in definitions. """
        simulator = DaikinSimulator()

        engine = sqlalchemy.create_engine('sqlite://')  # in-memory database
        sql.Base.metadata.create_all(engine)

        poller.poll_once(simulator, decoding.serial_page_prefix_to_decoders, engine)

        with sql.session_scope(engine) as session:
            self.assertEqual(1, session.query(sql.SerialState).count())
            state = session.query(sql.SerialState).one()

            # The simulator returns a response at random when there's more than one, so choose
            # a value to which the response is always the same:
            self.assertEqual(0x2, state.variable_values['47'], "Wrong decode for 47:O/U EEPROM (1st digit)")
            self.assertEqual(0x31, state.variable_values['48'], "Wrong decode for 48:O/U EEPROM (3rd 4th digit)")
            self.assertEqual(0x95, state.variable_values['49'], "Wrong decode for 49:O/U EEPROM (5th 6th digit)")
            self.assertEqual(0x1, state.variable_values['50'], "Wrong decode for 50:O/U EEPROM (7th 8th digit)")
            self.assertEqual(0x2, state.variable_values['51'], "Wrong decode for 51:O/U EEPROM (10th digit)")
            self.assertEqual(0x5, state.variable_values['52'], "Wrong decode for 52:O/U EEPROM (11th digit)")

    def test_espaltherma_definitions(self):
        """ Test that poll_once() works as expected using espaltherma definitions. """
        simulator = DaikinSimulator()

        definitions_file = os.path.join(DEFINITION_FILES, 'ALTHERMA(LT_CA_CB_04-08KW).h')
        with open(definitions_file) as f:
            definition_text = f.read()
        espaltherma_decoding_table = parse_espaltherma_definition(definition_text, output_text=False)

        engine = sqlalchemy.create_engine('sqlite://')  # in-memory database
        sql.Base.metadata.create_all(engine)

        poller.poll_once(simulator, espaltherma_decoding_table, engine)

        with sql.session_scope(engine) as session:
            self.assertEqual(1, session.query(sql.SerialState).count())
            state = session.query(sql.SerialState).one()

            # The simulator returns a response at random when there's more than one, so choose
            # a value to which the response is always the same:
            self.assertEqual(6.0, state.variable_values['00.12.105'], "21:O/U capacity (kW)")
