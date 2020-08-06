""" Database table mappings for the Daikin ASHP state. """

import sqlalchemy

from contextlib import contextmanager

from sqlalchemy import Column, JSON, Text  # Integer, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.schema import CreateColumn


TIMESTAMPTZ = sqlalchemy.types.TIMESTAMP(timezone=True)

Base = declarative_base()


@compiles(JSON, "postgresql")
def compile_json_postgresql(type_, compiler, **kw):
    return "JSONB"

@compiles(JSON, "sqlite")
def compile_json_sqlite(type_, compiler, **kw):
    return "TEXT"


class DaikinState(Base):
    """ Records the state of a Daikin ASHP at a particular time. """

    __tablename__ = 'daikin_ashp_state'

    timestamp = Column(TIMESTAMPTZ, primary_key=True)
    raw_page_contents = Column(JSON)
    variable_values = Column(JSON)

    def __repr__(self):
        """ Nicer repr. """
        return (
            f"<{self.__class__.__name__} {self.timestamp} {self.latest_variable_values}>"
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
