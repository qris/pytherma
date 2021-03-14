""" Tests for the poller module. """

import unittest

from pytherma import monitor, sql


class MonitorTest(unittest.TestCase):
    """ Tests for the P1/P2 monitor module. """

    def test_database_output_plugin(self):
        """ Test that the DatabaseOutputPlugin works as expected. """
        plugin = monitor.DatabaseOutputPlugin('sqlite://')  # # in-memory database
        plugin.initialise()

        example_400010_line = b'R 0.024: 400010010081013700180015001A000000000000400000 CRC=87'
        monitor.parse_line(example_400010_line, [plugin])

        with sql.session_scope(plugin.engine) as session:
            self.assertEqual(0, session.query(sql.P1P2State).count(),
                             "First line should not write any output to the database")

        monitor.parse_line(example_400010_line, [plugin])
        with sql.session_scope(plugin.engine) as session:
            self.assertEqual(1, session.query(sql.P1P2State).count(),
                             "Second line should write values accumulated during first round "
                             "to the database")
            record = session.query(sql.P1P2State).one()
            self.assertEqual(55, record.target_dhw_temp)
