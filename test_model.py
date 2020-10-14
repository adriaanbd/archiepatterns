from datetime import date, timedelta
from model import Batch, OrderLine
import pytest

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)

QUANTITY = 20
GREATER = 30
SMALLER = 10

def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch = Batch('order-ref', 'CRAZY_LAMP', QUANTITY)
    line = OrderLine('1', 'CRAZY_LAMP', SMALLER)
    batch.allocate(line)
    assert batch.qty == 10

def test_can_allocate_if_available_greater_than_required():
    batch = Batch('order-ref', 'CRAZY_LAMP', QUANTITY)
    line = OrderLine('1', 'CRAZY_LAMP', GREATER)
    batch.allocate(line)
    assert batch.qty == QUANTITY