from datetime import date, timedelta
from model import Batch, OrderLine
import pytest

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)

QUANTITY, GREATER, SMALLER = 20, 30, 10
SKU, BATCH_REF, ORDER_REF = 'CRAZY_LAMP', 'batch-ref', 'order-ref'

def make_batch_n_line(sku, batch_qty, line_qty):
    batch = Batch(BATCH_REF, sku, batch_qty, line_qty)
    line = OrderLine(ORDER_REF, sku, line_qty)
    return batch, line

def test_does_allocate_if_available_greater_than_required():
    batch, line = make_batch_n_line(SKU, QUANTITY, SMALLER)
    batch.allocate(line)
    assert batch.qty == QUANTITY - SMALLER

def test_doesnt_allocate_if_available_smaller_than_required():
    batch, line = make_batch_n_line(SKU, QUANTITY, GREATER)
    batch.allocate(line)
    assert batch.qty == QUANTITY

def test_does_allocate_if_available_equal_to_required():
    batch, line = make_batch_n_line(SKU, QUANTITY, QUANTITY)
    batch.allocate(line)
    assert batch.qty == 0

def test_doesnt_allocate_if_skus_do_not_match():
    batch = Batch(BATCH_REF, SKU, QUANTITY)
    line = OrderLine(ORDER_REF, 'SANE_LAMP', SMALLER)
    batch.allocate(line)
    assert batch.qty == QUANTITY