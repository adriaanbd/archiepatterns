import pytest
from datetime import date, timedelta
from model import Batch, OrderLine, allocate, OutOfStock
from pdb import set_trace

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)
IN_STOCK = "in-stock-batch"
SHIPMENT = "shipment-batch"
CLOCK, SPOON, FORK, POSTER = "CLOCK", "SPOON", "FORK", "POSTER"
BATCH1, ORDER1, ORDER2 = "batch1", "order1", "order2"
SPEEDY, NORMAL, SLOW = "speedy-batch", "normal-batch", "slow-batch"
OREF = "oref"

def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = Batch(IN_STOCK, CLOCK, 100, eta=None)
    shipment_batch = Batch(SHIPMENT, CLOCK, 100, eta=tomorrow)
    line = OrderLine(OREF, CLOCK, 10)

    allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_qty == 90
    assert shipment_batch.available_qty == 100

def test_prefers_earlier_batches():
    earliest = Batch(SPEEDY, SPOON, 100, eta=today)
    medium = Batch(NORMAL, SPOON, 100, eta=tomorrow)
    latest = Batch(SLOW, SPOON, 100, eta=later)
    line = OrderLine(ORDER1, SPOON, 10)

    allocate(line, [medium, earliest, latest])

    assert earliest.available_qty == 90
    assert medium.available_qty == 100
    assert latest.available_qty == 100

def test_returns_allocated_batch_ref():
    in_stock_batch = Batch("in-stock-batch-ref", POSTER, 100, eta=None)
    shipment_batch = Batch("shipment-batch-ref", POSTER, 100, eta=tomorrow)
    line = OrderLine(OREF, POSTER, 10)
    allocation = allocate(line, [in_stock_batch, shipment_batch])
    assert allocation == in_stock_batch.ref

def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = Batch(BATCH1, FORK, 10, eta=today)
    allocate(OrderLine(ORDER1, FORK, 10), [batch])

    with pytest.raises(OutOfStock, match=FORK):
        allocate(OrderLine(ORDER2, FORK, 1), [batch])