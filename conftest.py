import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from orm import metadata, start_mappers


@pytest.fixture
def in_memory_db():
    # creates instance of Engine, source of ddbb connectivity
    engine = create_engine('sqlite:///:memory:')
    metadata.create_all(engine)  # creates all tables in metadata
    return engine


@pytest.fixture
def session(in_memory_db):
    start_mappers()
    # factory to generate new Session objects
    yield sessionmaker(bind=in_memory_db)()  # bind the session to a connection
    clear_mappers()