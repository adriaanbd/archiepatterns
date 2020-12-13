from repository import SQLAlchemyRepository
from model import Batch, OrderLine

BATCH_1 = "batch1"
BATCH_2 = "batch2"
ORDER_1 = "order1"
SOFA = "SOFA"
SOAP = "SOAP"
TWELVE = 12
HUNDRED = 100


def insert_order_line(session):
    session.execute(
        'INSERT INTO order_lines (orderid, sku, qty)'
        f' VALUES ({ORDER_1}, {SOFA}, {TWELVE})'
    )
    [[orderline_id]] = session.execute(
        'SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku',
        dict(orderid=ORDER_1, sku=SOFA)
    )

    return orderline_id

def insert_batch(session, batch_id):
    session.execute(
        'INSERT INTO batches (reference, sku, _purchased_quantity, eta)'
        ' VALUES (:batch_id, "SOFA", 100, null)',
        dict(batch_id=batch_id)
    )
    [[batch_id]] = session.execute(
        'SELECT id FROM batches WHERE reference=:batch_id AND sku="SOFA"',
        dict(batch_id=batch_id)
    )
    return batch_id

def insert_allocation(session, orderline_id, batch_id):
    session.execute(
        'INSERT INTO allocations (orderline_id, batch_id)'
        ' VALUES (:orderline_id, :batch_id)',
        dict(orderline_id=orderline_id, batch_id=batch_id)
    )

def test_repository_can_save_a_batch(session):
    batch = Batch(BATCH_1, SOAP, HUNDRED, eta=None)
    repo = SQLAlchemyRepository(session)
    repo.add(batch)  # method under test
    session.commit()  # separate from repository (intentional)

    #  verify the data is saved
    rows = list(
        session.execute(
            'SELECT reference, sku, _purchases_quantity, eta ' \
            'FROM "batches"'
        )
    )

    assert rows == [(BATCH_1, SOAP, HUNDRED, None)]

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
