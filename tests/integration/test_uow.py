from allocation.service_layer import unit_of_work
from allocation.domain import model
import pytest

BATCH1, ORDER1, ORDER2 = "batch1", "order1", "order2"
REAL_SKU, UNREAL_SKU = "SKU_EXISTS", "SKU_DOESNT_EXIST"
MORE, LESS = 100, 10

def insert_batch(session, ref, sku, qty, eta):
    session.execute(
        'INSERT INTO batches (ref, sku, _qty, eta)'
        ' VALUES (:ref, :sku, :qty, :eta)',
        dict(ref=ref, sku=sku, qty=qty, eta=eta)
    )

def get_allocated_batch_ref(session, orderid, sku):
    [[orderlineid]] = session.execute(
        'SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku',
        dict(orderid=orderid, sku=sku)
    )
    [[batchref]] = session.execute(
        'SELECT b.ref FROM allocations JOIN batches AS b ON batch_id = b.id'
        ' WHERE orderline_id=:orderlineid',
        dict(orderlineid=orderlineid)
    )
    return batchref

def test_uow_can_retrieve_a_batch_and_allocate_to_it(session_factory):
    session = session_factory()
    insert_batch(session, BATCH1, REAL_SKU, MORE, None)
    session.commit()

    uow = unit_of_work.SQLAlchemyUnitOfWork(session_factory)
    with uow:
        batch = uow.batches.get(reference=BATCH1)
        line = model.OrderLine(ORDER1, REAL_SKU, LESS)
        batch.allocate(line)
        uow.commit()

    batchref = get_allocated_batch_ref(session, ORDER1, REAL_SKU)
    assert batchref == BATCH1

def test_rolls_back_uncommitted_work_by_default(session_factory):
    uow = unit_of_work.SQLAlchemyUnitOfWork(session_factory)
    with uow:
        insert_batch(uow.session, BATCH1, REAL_SKU, MORE, None)
    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []

def test_rolls_back_on_error(session_factory):
    class MyException(Exception):
        pass

    uow = unit_of_work.SQLAlchemyUnitOfWork(session_factory)
    with pytest.raises(MyException):
        with uow:
            insert_batch(uow.session, BATCH1, REAL_SKU, MORE, None)
            raise MyException()
    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []
