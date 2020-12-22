
import time
from pathlib import Path

import pytest
import requests
from requests.exceptions import ConnectionError
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from orm import metadata, start_mappers

import config


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


def wait_for_postgres_to_come_up(engine):
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            return engine.connect()
        except OperationalError:
            time.sleep(0.5)
    pytest.fail('Postgres never came up')


def wait_for_webapp_to_come_up():
    deadline = time.time() + 15
    url = config.get_api_url()
    while time.time() < deadline:
        try:
            return requests.get(url)
        except ConnectionError:
            time.sleep(0.7)
    pytest.fail('API never came up')



@pytest.fixture(scope='session')
def postgres_db():
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    metadata.create_all(engine)
    return engine


@pytest.fixture
def postgres_session(postgres_db):
    start_mappers()
    yield sessionmaker(bind=postgres_db)()
    clear_mappers()


@pytest.fixture
def add_stock(postgres_session):
    batches_added = set()
    skus_added = set()

    def _add_stock(lines):
        for ref, sku, qty, eta in lines:
            postgres_session.execute(
                'INSERT INTO batches (ref, sku, _qty, eta)'
                ' VALUES (:ref, :sku, :qty, :eta)',
                dict(ref=ref, sku=sku, qty=qty, eta=eta),
            )
            [[batch_id]] = postgres_session.execute(
                'SELECT id FROM batches WHERE ref=:ref AND sku=:sku',
                dict(ref=ref, sku=sku),
            )
            batches_added.add(batch_id)
            skus_added.add(sku)
        postgres_session.commit()

    yield _add_stock

    for batch_id in batches_added:
        postgres_session.execute(
            'DELETE FROM allocations WHERE batch_id=:batch_id',
            dict(batch_id=batch_id),
        )
        postgres_session.execute(
            'DELETE FROM batches WHERE id=:batch_id',
            dict(batch_id=batch_id),
        )
    for sku in skus_added:
        postgres_session.execute(
            'DELETE FROM order_lines WHERE sku=:sku',
            dict(sku=sku),
        )
        postgres_session.commit()


@pytest.fixture
def restart_api():
    (Path(__file__).parent / 'flask_app.py').touch()
    time.sleep(0.5)
    wait_for_webapp_to_come_up()