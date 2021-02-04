import pytest
from allocation.domain import model
from allocation.adapters import repository
from allocation.service_layer import services
from allocation.service_layer import unit_of_work
from typing import List
from datetime import date, timedelta

class FakeRepository(repository.AbstractRepository):

    def __init__(self, products):
        self._products = set(products)

    def add(self, product: model.Product) -> None:
        self._products.add(product)

    def get(self, sku: model.Sku) -> model.Product:
        return next(
            (product for product in self._products 
             if product.sku == sku), None)

    def list(self) -> List[model.Product]:
        return list(self._products)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self) -> None:
        self.products = FakeRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


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
    uow = FakeUnitOfWork()

    services.add_batch(BATCH_1, REAL_SKU, 100, None, uow)
    assert uow.products.get(REAL_SKU) is not None
    assert uow.committed


def test_returns_allocation():
    """
    Tests that the allocation service is able to allocate an OrderLine.
    """
    uow = FakeUnitOfWork()
    services.add_batch(BATCH_1, REAL_SKU, HIGH_NUM, None, uow)
    result = services.allocate(
        ORDER_1, REAL_SKU, LOW_NUM, uow)
    assert result == BATCH_1


def test_error_for_invalid_sku():
    uow = FakeUnitOfWork()

    services.add_batch(BATCH_1, REAL_SKU, HIGH_NUM, None, uow)
    with pytest.raises(services.InvalidSKU, match=f"Invalid SKU: {UNREAL_SKU}"):
        services.allocate(ORDER_1, UNREAL_SKU, LOW_NUM, uow)


def test_commits():
    uow = FakeUnitOfWork()

    services.add_batch(BATCH_1, REAL_SKU, HIGH_NUM, None, uow)
    services.allocate(ORDER_1, REAL_SKU, LOW_NUM, uow)
    assert uow.committed is True

@pytest.mark.skip
def test_deallocate_decrements_available_quantity():
    uow = FakeUnitOfWork()

    services.add_batch(BATCH_1, REAL_SKU, HIGH_NUM, None, uow)
    batch_ref = services.allocate(ORDER_1, REAL_SKU, LOW_NUM, uow)

    batch = uow.batches.get(batch_ref)
    services.deallocate(ORDER_1, REAL_SKU, LOW_NUM, batch_ref, uow)
    assert batch.available_qty == HIGH_NUM

@pytest.mark.skip
def test_trying_to_deallocate_unallocated_sku():
    uow = FakeUnitOfWork()

    services.add_batch(BATCH_1, REAL_SKU, HIGH_NUM, None, uow)

    with pytest.raises(model.UnallocatedSKU, match=f"Unallocated SKU: {UNREAL_SKU}"):
        services.deallocate(ORDER_1, REAL_SKU, LOW_NUM, UNREAL_SKU, uow)

@pytest.mark.skip
def test_prefers_current_stock_batches_to_shipments():
    uow = FakeUnitOfWork()

    services.add_batch(IN_STOCK, CLOCK, 100, today, uow)
    services.add_batch(SHIPMENT, CLOCK, 100, tomorrow, uow)

    services.allocate(ORDER_1, CLOCK, 10, uow)

    b1, b2 = uow.batches.get(IN_STOCK), uow.batches.get(SHIPMENT)
    assert b1.available_qty == 90
    assert b2.available_qty == 100

@pytest.mark.skip
def test_prefer_earlier_batches():
    uow = FakeUnitOfWork()

    services.add_batch(SPEEDY, SPOON, 100, today, uow)
    services.add_batch(NORMAL, SPOON, 100, tomorrow, uow)
    services.add_batch(SLOW, SPOON, 100, later, uow)

    services.allocate(ORDER_1, SPOON, 10, uow)

    b1, b2, b3 = uow.batches.get(SPEEDY), uow.batches.get(NORMAL), uow.batches.get(SLOW)
    assert b1.available_qty == 90
    assert b2.available_qty == 100
    assert b3.available_qty == 100

@pytest.mark.skip
def test_returns_allocated_batch_ref():
    uow = FakeUnitOfWork()

    services.add_batch("in-stock-batch-ref", POSTER, 100, None, uow)
    services.add_batch("shipment-batch-ref", POSTER, 100, tomorrow, uow)


    allocation = services.allocate(OREF, POSTER, 10, uow)
    assert allocation == "in-stock-batch-ref"

@pytest.mark.skip
def test_raises_out_of_stock_exception_if_cannot_allocate():
    uow = FakeUnitOfWork()

    services.add_batch(BATCH1, FORK, 10, today, uow)
    services.allocate(ORDER1, FORK, 10, uow)

    with pytest.raises(model.OutOfStock, match=FORK):
        services.allocate(ORDER2, FORK, 1, uow)

@pytest.mark.skip
def test_does_allocate_if_available_greater_than_required():
    uow = FakeUnitOfWork()

    services.add_batch(BATCH_REF, SKU, GREATER, None, uow)
    ref = services.allocate(ORDER_REF, SKU, QUANTITY, uow)

    batch = uow.batches.get(ref)
    assert batch.available_qty == QUANTITY - SMALLER

@pytest.mark.skip
def test_doesnt_allocate_if_available_smaller_than_required():
    uow = FakeUnitOfWork()

    services.add_batch(BATCH_REF, SKU, QUANTITY, None, uow)
    ref = services.allocate(ORDER_REF, SKU, SMALLER, uow)

    batch = None
    try:
        services.allocate(ORDER_REF, SKU, QUANTITY, uow)
    except model.OutOfStock:
        batch = uow.batches.get(ref)
    assert batch.available_qty == QUANTITY - SMALLER

@pytest.mark.skip
def test_does_allocate_if_available_equal_to_required():
    uow = FakeUnitOfWork()

    services.add_batch(BATCH_REF, SKU, QUANTITY, None, uow)
    ref = services.allocate(ORDER_1, SKU, QUANTITY, uow)
    batch = uow.batches.get(ref)
    assert batch.available_qty == 0

@pytest.mark.skip
def test_doesnt_allocate_if_skus_do_not_match():
    uow = FakeUnitOfWork()

    services.add_batch(BATCH_REF, REAL_SKU, QUANTITY, None, uow)
    ref = services.allocate(ORDER_REF, REAL_SKU, SMALLER, uow)
    batch = None  # avoid batch being possibly unbound
    try:
        services.allocate(ORDER_REF, UNREAL_SKU, SMALLER, uow)
    except services.InvalidSKU or model.UnallocatedSKU:
        batch = uow.batches.get(ref)

    assert batch.available_qty == QUANTITY - SMALLER

@pytest.mark.skip
def test_can_only_deallocate_allocated_lines():
    uow = FakeUnitOfWork()

    services.add_batch(BATCH_REF, REAL_SKU, QUANTITY, None, uow)
    batch = None  # avoid batch being possibly unbound
    try:
        services.deallocate(ORDER_REF, SKU, SMALLER, BATCH_REF, uow)
    except model.UnallocatedSKU:
        batch = uow.batches.get(BATCH_REF)

    assert batch.available_qty == QUANTITY

@pytest.mark.skip
def test_allocation_is_idempotent():
    uow = FakeUnitOfWork()
    services.add_batch(BATCH_REF, SKU, QUANTITY, None, uow)
    services.allocate(ORDER_REF, SKU, SMALLER, uow)
    services.allocate(ORDER_REF, SKU, SMALLER, uow)

    batch = uow.batches.get(BATCH_REF)

    assert batch.available_qty == QUANTITY - SMALLER

@pytest.mark.skip
def test_change_batch_qty():
    uow = FakeUnitOfWork()

    services.add_batch(BATCH_REF, REAL_SKU, 100, None, uow)
    services.allocate(ORDER_REF, REAL_SKU, 70, uow)

    batch = uow.batches.get(BATCH_REF)
    assert batch.available_qty == 100 - 70

    services.change_batch_quantity(BATCH_REF, 30, uow)

    assert batch.available_qty > 0