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

    def get(self, ref: model.Sku) -> model.Batch:
        return next(b for b in self._batches if b.ref == ref)

    def list(self) -> List[model.Batch]:
        return list(self._batches)


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
today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)

def test_returns_allocation():
    """
    Tests that the allocation service is able to allocate an OrderLine.
    """
    line = model.OrderLine(ORDER_1, REAL_SKU, LOW_NUM)
    batch = model.Batch(BATCH_1, REAL_SKU, HIGH_NUM, eta=None)
    repo = FakeRepository([batch])

    result = services.allocate(line, repo, FakeSession())
    assert result == BATCH_1

def test_error_for_invalid_sku():
    line = model.OrderLine(ORDER_1, UNREAL_SKU, LOW_NUM)
    batch = model.Batch(BATCH_1, REAL_SKU, HIGH_NUM, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(services.InvalidSKU, match=f"Invalid SKU: {UNREAL_SKU}"):
        services.allocate(line, repo, session=FakeSession())

def test_commits():
    line = model.OrderLine(ORDER_1, REAL_SKU, LOW_NUM)
    batch = model.Batch(BATCH_1, REAL_SKU, HIGH_NUM, eta=None)
    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocate(line, repo, session)
    assert session.committed is True

def test_deallocate_decrements_available_quantity():
    line = model.OrderLine(ORDER_1, REAL_SKU, LOW_NUM)
    batch = model.Batch(BATCH_1, REAL_SKU, HIGH_NUM, None)
    repo, session = FakeRepository([batch]), FakeSession()
    batch_ref = services.allocate(line, repo, session)
    assert batch.available_qty == HIGH_NUM - LOW_NUM
    services.deallocate(line, batch_ref, repo, session)
    assert batch.available_qty == HIGH_NUM

def test_trying_to_deallocate_unallocated_sku():
    line = model.OrderLine(ORDER_1, UNREAL_SKU, LOW_NUM)
    batch = model.Batch(BATCH_1, REAL_SKU, HIGH_NUM, None)
    repo, session = FakeRepository([batch]), FakeSession()
    with pytest.raises(services.UnallocatedSKU,
                       match=f"Unallocated SKU: {UNREAL_SKU}"):
        services.deallocate(line, batch.ref, repo, session)

def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = model.Batch(IN_STOCK, CLOCK, 100, eta=None)
    shipment_batch = model.Batch(SHIPMENT, CLOCK, 100, eta=tomorrow)
    repo = FakeRepository([in_stock_batch, shipment_batch])
    sesh = FakeSession()

    line = model.OrderLine(ORDER_1, CLOCK, 10)

    services.allocate(line, repo, sesh)

    assert in_stock_batch.available_qty == 90
    assert shipment_batch.available_qty == 100

def test_prefers_earlier_batches():
    earliest = model.Batch(SPEEDY, SPOON, 100, eta=today)
    medium = model.Batch(NORMAL, SPOON, 100, eta=tomorrow)
    latest = model.Batch(SLOW, SPOON, 100, eta=later)
    line = model.OrderLine(ORDER1, SPOON, 10)

    repo = FakeRepository([medium, earliest, latest])
    sesh = FakeSession()

    services.allocate(line, repo, sesh)

    assert earliest.available_qty == 90
    assert medium.available_qty == 100
    assert latest.available_qty == 100

def test_returns_allocated_batch_ref():
    in_stock_batch = model.Batch("in-stock-batch-ref", POSTER, 100, eta=None)
    shipment_batch = model.Batch("shipment-batch-ref", POSTER, 100, eta=tomorrow)
    line = model.OrderLine(OREF, POSTER, 10)

    repo = FakeRepository([in_stock_batch, shipment_batch])
    sesh = FakeSession()

    allocation = services.allocate(line, repo, sesh)
    assert allocation == in_stock_batch.ref

def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = model.Batch(BATCH1, FORK, 10, eta=today)
    allocated_line = model.OrderLine(ORDER1, FORK, 10)
    unallocated_line = model.OrderLine(ORDER2, FORK, 1)

    repo = FakeRepository([batch])
    sesh = FakeSession()

    services.allocate(allocated_line, repo, sesh)

    with pytest.raises(model.OutOfStock, match=FORK):
        services.allocate(unallocated_line, repo, sesh)