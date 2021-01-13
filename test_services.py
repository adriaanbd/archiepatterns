from conftest import session  # is this session being used?
import pytest
from repository import AbstractRepository
import model
import services
from typing import List
from datetime import date, timedelta

class FakeRepository(AbstractRepository):

    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch: model.Batch) -> None:
        self._batches.add(batch)

    def get(self, ref: model.Ref) -> model.Batch:
        try:
            return next(b for b in self._batches if b.ref == ref)
        except StopIteration:
            raise model.UnallocatedSKU(f'Unallocated SKU: {ref}')

    def list(self) -> List[model.Batch]:
        return list(self._batches)

    @staticmethod
    def for_batch(ref, sku, qty, eta=None):
        """Factory for making a Repository with a Batch."""
        repo = FakeRepository([model.Batch(ref, sku, qty, eta)])
        return repo


class FakeSession():
    committed = False

    def commit(self):
        self.committed = True


class FakeUnitOfWork():
    def __init__(self) -> None:
        self.batches = FakeRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

ORDER_1, BATCH_1 = "O1", "B1"
REAL_SKU, UNREAL_SKU = "SKU_EXISTS", "SKU_DOESNT_EXIST"
IN_STOCK = "IN_STOCK_BATCH"
SHIPMENT = "SHIPMENT-BATCH"
LOW_NUM, HIGH_NUM = 10, 100
CLOCK, SPOON, FORK, POSTER = "CLOCK", "SPOON", "FORK", "POSTER"
BATCH1, ORDER1, ORDER2 = "batch1", "order1", "order2"
SPEEDY, NORMAL, SLOW = "speedy-batch", "normal-batch", "slow-batch"
OREF = "oref"
QUANTITY, GREATER, SMALLER = 20, 30, 10
SKU, BATCH_REF, ORDER_REF = 'CRAZY_LAMP', 'batch-ref', 'order-ref'
today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def test_add_batch():
    # repo, session = FakeRepository([]), FakeSession()
    uow = FakeUnitOfWork()
    services.add_batch(BATCH_1, REAL_SKU, 100, None, uow)
    # assert repo.get(BATCH_1) is not None
    assert uow.batches.get(BATCH_1) is not None
    # assert session.committed
    assert uow.committed

def test_returns_allocation():
    """
    Tests that the allocation service is able to allocate an OrderLine.
    """
    # repo = FakeRepository.for_batch(BATCH_1, REAL_SKU, HIGH_NUM, eta=None)
    # repo, session = FakeRepository([]), FakeSession()
    uow = FakeUnitOfWork()
    services.add_batch(BATCH_1, REAL_SKU, HIGH_NUM, None, uow)
    result = services.allocate(
        ORDER_1, REAL_SKU, LOW_NUM, uow)
    assert result == BATCH_1

def test_error_for_invalid_sku():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch(BATCH_1, REAL_SKU, HIGH_NUM, None, repo, session)
    with pytest.raises(services.InvalidSKU, match=f"Invalid SKU: {UNREAL_SKU}"):
        services.allocate(ORDER_1, UNREAL_SKU, LOW_NUM, repo, session)

def test_commits():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch(BATCH_1, REAL_SKU, HIGH_NUM, None, repo, session)
    services.allocate(ORDER_1, REAL_SKU, LOW_NUM, repo, session)
    assert session.committed is True

def test_deallocate_decrements_available_quantity():
    repo, session = FakeRepository([]), FakeSession()

    services.add_batch(BATCH_1, REAL_SKU, HIGH_NUM, None, repo, session)
    batch_ref = services.allocate(ORDER_1, REAL_SKU, LOW_NUM, repo, session)

    batch = repo.get(batch_ref)
    services.deallocate(ORDER_1, REAL_SKU, LOW_NUM, batch_ref, repo, session)
    assert batch.available_qty == HIGH_NUM

def test_trying_to_deallocate_unallocated_sku():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch(BATCH_1, REAL_SKU, HIGH_NUM, None, repo, session)

    with pytest.raises(model.UnallocatedSKU, match=f"Unallocated SKU: {UNREAL_SKU}"):
        services.deallocate(ORDER_1, REAL_SKU, LOW_NUM, UNREAL_SKU, repo, session)

def test_prefers_current_stock_batches_to_shipments():
    repo, session = FakeRepository([]), FakeSession()

    services.add_batch(IN_STOCK, CLOCK, 100, today, repo, session)
    services.add_batch(SHIPMENT, CLOCK, 100, tomorrow, repo, session)

    services.allocate(ORDER_1, CLOCK, 10, repo, session)

    b1, b2 = repo.get(IN_STOCK), repo.get(SHIPMENT)
    assert b1.available_qty == 90
    assert b2.available_qty == 100

def test_prefer_earlier_batches():
    repo, session = FakeRepository([]), FakeSession()

    services.add_batch(SPEEDY, SPOON, 100, today, repo, session)
    services.add_batch(NORMAL, SPOON, 100, tomorrow, repo, session)
    services.add_batch(SLOW, SPOON, 100, later, repo, session)

    services.allocate(ORDER_1, SPOON, 10, repo, session)

    b1, b2, b3 = repo.get(SPEEDY), repo.get(NORMAL), repo.get(SLOW)
    assert b1.available_qty == 90
    assert b2.available_qty == 100
    assert b3.available_qty == 100

def test_returns_allocated_batch_ref():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("in-stock-batch-ref", POSTER, 100, None, repo, session)
    services.add_batch("shipment-batch-ref", POSTER, 100, tomorrow, repo, session)


    allocation = services.allocate(OREF, POSTER, 10, repo, session)
    assert allocation == "in-stock-batch-ref"

def test_raises_out_of_stock_exception_if_cannot_allocate():
    repo, session = FakeRepository([]), FakeSession()

    services.add_batch(BATCH1, FORK, 10, today, repo, session)
    services.allocate(ORDER1, FORK, 10, repo, session)

    with pytest.raises(model.OutOfStock, match=FORK):
        services.allocate(ORDER2, FORK, 1, repo, session)

def test_does_allocate_if_available_greater_than_required():
    # repo = FakeRepository.for_batch(BATCH_REF, SKU, GREATER)
    repo, session = FakeRepository([]), FakeSession()

    services.add_batch(BATCH_REF, SKU, GREATER, None, repo, session)
    ref = services.allocate(ORDER_REF, SKU, QUANTITY, repo, session)

    batch = repo.get(ref)
    assert batch.available_qty == QUANTITY - SMALLER

def test_doesnt_allocate_if_available_smaller_than_required():
    repo, session = FakeRepository([]), FakeSession()

    services.add_batch(BATCH_REF, SKU, QUANTITY, None, repo, session)
    ref = services.allocate(ORDER_REF, SKU, SMALLER, repo, session)

    try:
        services.allocate(ORDER_REF, SKU, QUANTITY, repo, session)
    except model.OutOfStock:
        batch = repo.get(ref)
        assert batch.available_qty == QUANTITY - SMALLER

def test_does_allocate_if_available_equal_to_required():
    repo, session = FakeRepository([]), FakeSession()

    services.add_batch(BATCH_REF, SKU, QUANTITY, None, repo, session)
    ref = services.allocate(ORDER_1, SKU, QUANTITY, repo, session)
    batch = repo.get(ref)
    assert batch.available_qty == 0

def test_doesnt_allocate_if_skus_do_not_match():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch(BATCH_REF, REAL_SKU, QUANTITY, None, repo, session)
    ref = services.allocate(ORDER_REF, REAL_SKU, SMALLER, repo, session)
    try:
        services.allocate(ORDER_REF, UNREAL_SKU, SMALLER, repo, session)
    except services.InvalidSKU or model.UnallocatedSKU:
        batch = repo.get(ref)
        assert batch.available_qty == QUANTITY - SMALLER

def test_can_only_deallocate_allocated_lines():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch(BATCH_REF, REAL_SKU, QUANTITY, None, repo, session)
    try:
        services.deallocate(ORDER_REF, SKU, SMALLER, BATCH_REF, repo, session)
    except model.UnallocatedSKU:
        batch = repo.get(BATCH_REF)
        assert batch.available_qty == QUANTITY

def test_allocation_is_idempotent():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch(BATCH_REF, SKU, QUANTITY, None, repo, session)
    services.allocate(ORDER_REF, SKU, SMALLER, repo, session)
    services.allocate(ORDER_REF, SKU, SMALLER, repo, session)

    batch = repo.get(BATCH_REF)
    assert batch.available_qty == QUANTITY - SMALLER