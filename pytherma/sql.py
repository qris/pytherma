""" Database table mappings for the Daikin ASHP state. """

import sqlalchemy

from contextlib import contextmanager

from sqlalchemy import Boolean, Column, JSON, Numeric  # Integer, Text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


TIMESTAMPTZ = sqlalchemy.types.TIMESTAMP(timezone=True)

Base = declarative_base()


@compiles(JSON, "postgresql")
def compile_json_postgresql(type_, compiler, **kw):
    """ Override JSON type on Postgres to use JSONB. """
    return "JSONB"


@compiles(JSON, "sqlite")
def compile_json_sqlite(type_, compiler, **kw):
    """ Override JSON type on SQLite to use Text. """
    return "TEXT"


class SerialState(Base):
    """ Records the state of a Daikin ASHP at a particular time. """

    __tablename__ = 'daikin_serial_state'

    timestamp = Column(TIMESTAMPTZ, primary_key=True)
    raw_page_contents = Column(JSON)
    variable_values = Column(JSON)

    def __repr__(self):
        """ Nicer repr. """
        return (
            f"<{self.__class__.__name__} {self.timestamp} {self.variable_values}>"
        )


class P1P2State(Base):
    """ Records the state of all Daikin P1/P2 bus devices at a particular time. """

    __tablename__ = 'daikin_p1p2_state'

    timestamp = Column(TIMESTAMPTZ, primary_key=True)
    raw_packets_contents = Column(JSON)
    dhw_booster = Column(Boolean)
    dhw_heating = Column(Boolean)
    lwt_control = Column(Boolean)
    heating_enabled = Column(Boolean)
    heating_on = Column(Boolean)
    cooling_on = Column(Boolean)
    main_zone = Column(Boolean)
    additional_zone = Column(Boolean)
    dhw_tank = Column(Boolean)
    threeway_on_off = Column(Boolean)
    threeway_tank = Column(Boolean)
    target_dhw_temp = Column(Numeric(3, 2))
    target_room_temp = Column(Numeric(3, 2))
    quiet_mode = Column(Boolean)
    compressor_on = Column(Boolean)
    pump_on = Column(Boolean)
    dhw_active = Column(Boolean)

    def __repr__(self):
        """ Nicer repr. """
        return (
            f"<{self.__class__.__name__} {self.timestamp}>"
        )


@contextmanager
def session_scope(engine):
    """ Provide a transactional scope around a series of operations. """
    # https://stackoverflow.com/a/29805305/648162
    session = sessionmaker(bind=engine)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
