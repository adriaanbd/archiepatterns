from conftest import session
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
        repo = FakeRepository([model.Batch(ref, sku, qty, eta)])
        return repo


class FakeSession():
    committed = False

    def commit(self):
        self.committed = True


ORDER_1, BATCH_1 = "O1", "B1"
REAL_SKU, UNREAL_SKU = "SKU_EXISTS", "SKU_DOESNT_EXIST"
IN_STOCK = "IN_STOCK_BACK"
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

def test_returns_allocation():
    """
    Tests that the allocation service is able to allocate an OrderLine.
    """
    repo = FakeRepository.for_batch(BATCH_1, REAL_SKU, HIGH_NUM, eta=None)

    result = services.allocate(
        ORDER_1, REAL_SKU, LOW_NUM, repo, FakeSession())
    assert result == BATCH_1

def test_error_for_invalid_sku():
    repo = FakeRepository.for_batch(BATCH_1, REAL_SKU, HIGH_NUM, eta=None)

    with pytest.raises(services.InvalidSKU, match=f"Invalid SKU: {UNREAL_SKU}"):
        services.allocate(ORDER_1, UNREAL_SKU, LOW_NUM, repo, FakeSession())

def test_commits():
    repo = FakeRepository.for_batch(BATCH_1, REAL_SKU, HIGH_NUM, eta=None)
    session = FakeSession()
    services.allocate(ORDER_1, REAL_SKU, LOW_NUM, repo, session)
    assert session.committed is True

def test_deallocate_decrements_available_quantity():
    repo = FakeRepository.for_batch(BATCH_1, REAL_SKU, HIGH_NUM, None)
    sesh = FakeSession()
    batch_ref = services.allocate(ORDER_1, REAL_SKU, LOW_NUM, repo, sesh)

    batch = repo.get(batch_ref)
    services.deallocate(ORDER_1, REAL_SKU, LOW_NUM, batch_ref, repo, sesh)
    assert batch.available_qty == HIGH_NUM

def test_trying_to_deallocate_unallocated_sku():
    repo = FakeRepository.for_batch(BATCH_1, REAL_SKU, HIGH_NUM, None)
    session = FakeSession()

    with pytest.raises(model.UnallocatedSKU, match=f"Unallocated SKU: {UNREAL_SKU}"):
        services.deallocate(ORDER_1, REAL_SKU, LOW_NUM, UNREAL_SKU, repo, session)

def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = model.Batch(IN_STOCK, CLOCK, 100, eta=None)
    shipment_batch = model.Batch(SHIPMENT, CLOCK, 100, eta=tomorrow)
    repo = FakeRepository([in_stock_batch, shipment_batch])
    sesh = FakeSession()

    services.allocate(ORDER_1, CLOCK, 10, repo, sesh)

    assert in_stock_batch.available_qty == 90
    assert shipment_batch.available_qty == 100

def test_prefers_earlier_batches():
    earliest = model.Batch(SPEEDY, SPOON, 100, eta=today)
    medium = model.Batch(NORMAL, SPOON, 100, eta=tomorrow)
    latest = model.Batch(SLOW, SPOON, 100, eta=later)

    repo = FakeRepository([medium, earliest, latest])
    sesh = FakeSession()

    services.allocate(ORDER1, SPOON, 10, repo, sesh)

    assert earliest.available_qty == 90
    assert medium.available_qty == 100
    assert latest.available_qty == 100

def test_returns_allocated_batch_ref():
    in_stock_batch = model.Batch("in-stock-batch-ref", POSTER, 100, eta=None)
    shipment_batch = model.Batch("shipment-batch-ref", POSTER, 100, eta=tomorrow)

    repo = FakeRepository([in_stock_batch, shipment_batch])
    sesh = FakeSession()

    allocation = services.allocate(OREF, POSTER, 10, repo, sesh)
    assert allocation == in_stock_batch.ref

def test_raises_out_of_stock_exception_if_cannot_allocate():
    repo = FakeRepository.for_batch(BATCH1, FORK, 10, eta=today)
    sesh = FakeSession()

    services.allocate(ORDER1, FORK, 10, repo, sesh)

    with pytest.raises(model.OutOfStock, match=FORK):
        services.allocate(ORDER2, FORK, 1, repo, sesh)

def make_batch_n_line(sku, batch_qty, line_qty):
    batch = model.Batch(BATCH_REF, sku, batch_qty)
    line = model.OrderLine(ORDER_REF, sku, line_qty)
    return batch, line

def test_does_allocate_if_available_greater_than_required():
    repo = FakeRepository.for_batch(BATCH_REF, SKU, GREATER)
    sesh = FakeSession()

    ref = services.allocate(ORDER_REF, SKU, QUANTITY, repo, sesh)

    batch = repo.get(ref)
    print(batch.available_qty)
    assert batch.available_qty == QUANTITY - SMALLER

def test_doesnt_allocate_if_available_smaller_than_required():
    repo = FakeRepository.for_batch(BATCH_REF, SKU, QUANTITY)
    sesh = FakeSession()
    ref = services.allocate(ORDER_REF, SKU, SMALLER, repo, sesh)

    try:
        services.allocate(ORDER_REF, SKU, QUANTITY, repo, sesh)
    except model.OutOfStock:
        batch = repo.get(ref)
        assert batch.available_qty == QUANTITY - SMALLER

def test_does_allocate_if_available_equal_to_required():
    repo = FakeRepository.for_batch(BATCH_REF, SKU, QUANTITY)
    sesh = FakeSession()

    ref = services.allocate(ORDER_1, SKU, QUANTITY, repo, sesh)
    batch = repo.get(ref)
    assert batch.available_qty == 0

def test_doesnt_allocate_if_skus_do_not_match():
    repo = FakeRepository.for_batch(BATCH_REF, REAL_SKU, QUANTITY)
    sesh = FakeSession()
    ref = services.allocate(ORDER_REF, REAL_SKU, SMALLER, repo, sesh)
    try:
        services.allocate(ORDER_REF, UNREAL_SKU, SMALLER, repo, sesh)
    except services.InvalidSKU or model.UnallocatedSKU:
        batch = repo.get(ref)
        assert batch.available_qty == QUANTITY - SMALLER

def test_can_only_deallocate_allocated_lines():
    repo = FakeRepository.for_batch(BATCH_REF, SKU, QUANTITY)
    sesh = FakeSession()

    try:
        services.deallocate(ORDER_REF, SKU, SMALLER, BATCH_REF, repo, sesh)
    except model.UnallocatedSKU:
        batch = repo.get(BATCH_REF)
        assert batch.available_qty == QUANTITY

def test_allocation_is_idempotent():
    repo = FakeRepository.for_batch(BATCH_REF, SKU, QUANTITY)
    sesh = FakeSession()

    services.allocate(ORDER_REF, SKU, SMALLER, repo, sesh)
    services.allocate(ORDER_REF, SKU, SMALLER, repo, sesh)

    batch = repo.get(BATCH_REF)
    assert batch.available_qty == QUANTITY - SMALLER

def test_add_batch():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch(BATCH_1, REAL_SKU,   100, None, repo, session)
    assert repo.get(BATCH_1) is not None
    assert session.committed