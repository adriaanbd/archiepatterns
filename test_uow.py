import unit_of_work
import model

BATCH1, ORDER1, ORDER2 = "batch1", "order1", "order2"
REAL_SKU, UNREAL_SKU = "SKU_EXISTS", "SKU_DOESNT_EXIST"
MORE, LESS = 100, 10

def insert_batch(session, ref, sku, qty, eta):
    session.execute(
        'INSERT INTO batches (ref, sku, _qty, eta)'
        ' VALUES (:ref, :sku, :qty, :eta)',
        dict(ref=ref, sku=sku, qty=qty, eta=eta)
    )

def test_uow_can_retrieve_a_batch_and_allocate_to_it(session_factory):
    session = session_factory()
    insert_batch(session, BATCH1, REAL_SKU, MORE, None)
    session.commit()

    uow = unit_of_work.SQLAlchemyUnitOfWork(session)
    with uow:
        batch = uow.batches.get(reference=BATCH1)
        line = model.OrderLine(ORDER1, REAL_SKU, LESS)
        batch.allocate(line)
        uow.commit()
        assert uow.committed