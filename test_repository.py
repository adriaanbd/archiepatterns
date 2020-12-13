from repository import SQLAlchemyRepository
from model import Batch, OrderLine

BATCH_1 = "batch1"
BATCH_2 = "batch2"
ORDER_1 = "order1"
SOFA = "SOFA"
SOAP = "SOAP"
BENCH = "BENCH"
TWELVE = 12
HUNDRED = 100

def test_repository_can_save_a_batch(session):
    batch = Batch(BATCH_1, SOAP, HUNDRED, eta=None)
    repo = SQLAlchemyRepository(session)
    repo.add(batch)  # method under test
    # https://docs.sqlalchemy.org/en/13/orm/session_basics.html#committing
    session.commit()  # separate from repository (intentional), it
    # flushes pending changes and commits the current transaction.

    #  verify the data is saved
    rows = list(
        # https://docs.sqlalchemy.org/en/13/orm/session_api.html#sqlalchemy.orm.session.Session.execute
        session.execute( # Execute a SQL expression construct or string statement within the current transaction
            'SELECT ref, sku, _qty, eta ' \
            'FROM "batches"'
        )
    )

    assert rows == [(BATCH_1, SOAP, HUNDRED, None)]

def insert_order_line(session):
    session.execute(
        'INSERT INTO order_lines (orderid, sku, qty)'
        f' VALUES ("{ORDER_1}", "{SOFA}", "{TWELVE}")'
    )
    [[orderline_id]] = session.execute(
        f'SELECT id FROM order_lines WHERE orderid="{ORDER_1}" AND sku="{SOFA}"',
    )

    return orderline_id

def insert_batch(session, batch_id):
    session.execute(
        'INSERT INTO batches (ref, sku, _qty, eta)'
        f' VALUES ("{batch_id}", "{SOFA}", "{HUNDRED}", null)',
    )
    [[batch_id]] = session.execute(
        f'SELECT id FROM batches WHERE ref="{batch_id}" AND sku="{SOFA}"'
    )
    return batch_id

def insert_allocation(session, orderline_id, batch_id):
    session.execute(
        'INSERT INTO allocations (orderline_id, batch_id)'
        f' VALUES ("{orderline_id}", "{batch_id}")',
    )

def test_repository_can_retrieve_a_batch_with_allocations(session):
    orderline_id = insert_order_line(session)
    batch1_id = insert_batch(session, BATCH_1)
    insert_batch(session, BATCH_2)
    insert_allocation(session, orderline_id, batch1_id)

    repo = SQLAlchemyRepository(session)
    retrieved = repo.get(BATCH_1)  # tests the read side

    expected = Batch(BATCH_1, SOFA, HUNDRED, eta=None)
    assert retrieved == expected  # tests object equality
    assert retrieved.sku == expected.sku
    assert retrieved._qty == expected._qty
    assert retrieved._allocations == {
        OrderLine(ORDER_1, SOFA, TWELVE),
    }

def get_allocations(session, batchid):
    rows = list(session.execute(
        'SELECT orderid'
        ' FROM allocations'
        ' JOIN order_lines ON allocations.orderline_id = order_lines.id'
        ' JOIN batches ON allocations.batch_id = batches.id'
        ' WHERE batches.ref = :batchid',
        dict(batchid=batchid)
    ))
    return {row[0] for row in rows}


def test_updating_a_batch(session):
    order1 = OrderLine(ORDER_1, BENCH, 10)
    order2 = OrderLine('order2', BENCH, 20)
    batch = Batch(BATCH_1, BENCH, 100, eta=None)
    batch.allocate(order1)

    repo = SQLAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    batch.allocate(order2)
    repo.add(batch)
    session.commit()

    assert get_allocations(session, BATCH_1) == {ORDER_1, 'order2'}
