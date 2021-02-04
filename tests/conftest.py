
import time
from pathlib import Path

import pytest
import requests
from requests.exceptions import ConnectionError

from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

from allocation.adapters import orm
from allocation import config


@pytest.fixture
def in_memory_db():
    # creates an Engine instance, source of ddbb connectivity and
    # behavior by connecting a Pool and Dialect object together
    engine = create_engine('sqlite:///:memory:')
    # https://docs.sqlalchemy.org/en/13/core/metadata.html#metadata-describing
    orm.metadata.create_all(engine)  # checks existence of each table, and
    # if not found, issues CREATE statements for all tables stored herein
    # will not attempt to recreate tables by default.
    # first argument is bind that accepts a Connectable object, which can be:
    # Connection and Engine objects.
    return engine

@pytest.fixture
def session_factory(in_memory_db):
    orm.start_mappers()
    # factory to generate new Session objects:
    # https://docs.sqlalchemy.org/en/14/orm/session_api.html#sqlalchemy.orm.sessionmaker
    yield sessionmaker(bind=in_memory_db)  # bind the session to a connection
    # https://docs.sqlalchemy.org/en/14/orm/mapping_api.html#sqlalchemy.orm.clear_mappers
    clear_mappers()  # remove all mappers from all classes, not for normal use, b/c:
    # Normally, mappers are permanent structural components of user-defined classes,
    # and are never discarded independently of their class. If a mapped class itself
    # is garbage collected, its mapper is automatically disposed of as well.
    # As such, it is only for usage in test suites that re-use the same classes with
    # different mappings, which is itself an extremely rare use case

@pytest.fixture
def session(session_factory):
    return session_factory()

def wait_for_postgres_to_come_up(engine):
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            return engine.connect()
        except OperationalError:
            time.sleep(0.7)
    pytest.fail('Postgres never came up')

def wait_for_webapp_to_come_up():
    deadline = time.time() + 10
    url = config.get_api_url()
    while time.time() < deadline:
        try:
            return requests.get(url)
        except ConnectionError:
            time.sleep(0.5)
    pytest.fail('API never came up')

@pytest.fixture(scope='session')
def postgres_db():
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    orm.metadata.create_all(engine)
    return engine

@pytest.fixture
def postgres_session_factory(postgres_db):
    orm.start_mappers()
    yield sessionmaker(bind=postgres_db)()
    clear_mappers()

@pytest.fixture
def postgres_session(postgres_db):
    return postgres_session_factory()

@pytest.fixture
def restart_api():
    # touch:
    # Create a file at this given path. If the file already exists, the
    # function succeeds if exist_ok is true (and its modification time is
    # updated to the current time), otherwise FileExistsError is raised.
    (Path(__file__).parent / 'flask_app.py').touch()  # parent: the logical parent of the path
    time.sleep(0.5)
    wait_for_webapp_to_come_up()