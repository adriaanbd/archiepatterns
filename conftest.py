import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from orm import metadata, start_mappers


@pytest.fixture
def in_memory_db():
    # creates an Engine instance, source of ddbb connectivity and
    # behavior by connecting a Pool and Dialect object together
    engine = create_engine('sqlite:///:memory:')
    # https://docs.sqlalchemy.org/en/13/core/metadata.html#metadata-describing
    metadata.create_all(engine)  # checks existence of each table, and
    # if not found, issues CREATE statements for all tables stored herein
    # will not attempt to recreate tables by default.
    # first argument is bind that accepts a Connectable object, which can be:
    # Connection and Engine objects.
    return engine


@pytest.fixture
def session(in_memory_db):
    start_mappers()
    # factory to generate new Session objects:
    # https://docs.sqlalchemy.org/en/14/orm/session_api.html#sqlalchemy.orm.sessionmaker
    yield sessionmaker(bind=in_memory_db)()  # bind the session to a connection
    # https://docs.sqlalchemy.org/en/14/orm/mapping_api.html#sqlalchemy.orm.clear_mappers
    clear_mappers()  # remove all mappers from all classes, not for normal use, b/c:
    # Normally, mappers are permanent structural components of user-defined classes,
    # and are never discarded independently of their class. If a mapped class itself
    # is garbage collected, its mapper is automatically disposed of as well.
    # As such, it is only for usage in test suites that re-use the same classes with
    # different mappings, which is itself an extremely rare use case