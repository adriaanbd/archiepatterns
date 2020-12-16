from conftest import session
import pytest
from repository import AbstractRepository
from model import OrderLine, Batch, Sku
from services import allocate, InvalidSKU, add_batch, deallocate
from typing import List


class FakeRepository(AbstractRepository):

    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch: Batch) -> None:
        self._batches.add(batch)

    def get(self, ref: Sku) -> Batch:
        return next(b for b in self._batches if b.ref == ref)

    def list(self) -> List[Batch]:
        return list(self._batches)


class FakeSession():
    committed = False

    def commit(self):
        self.committed = True


ORDER_1, BATCH_1 = "o1", "b1"
REAL_SKU, UNREAL_SKU = "SKU_EXISTS", "SKU_DOESNT_EXIST"
LOW_NUM, HIGH_NUM = 10, 100

def test_returns_allocation():
    """
    Tests that the allocation service is able to allocate an OrderLine.
    """
    line = OrderLine(ORDER_1, REAL_SKU, LOW_NUM)
    batch = Batch(BATCH_1, REAL_SKU, HIGH_NUM, eta=None)
    repo = FakeRepository([batch])

    result = allocate(line, repo, FakeSession())
    assert result == BATCH_1

def test_error_for_invalid_sku():
    line = OrderLine(ORDER_1, UNREAL_SKU, LOW_NUM)
    batch = Batch(BATCH_1, REAL_SKU, HIGH_NUM, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(InvalidSKU, match=f"Invalid SKU: {UNREAL_SKU}"):
        allocate(line, repo, session=FakeSession())

def test_commits():
    line = OrderLine(ORDER_1, REAL_SKU, LOW_NUM)
    batch = Batch(BATCH_1, REAL_SKU, HIGH_NUM, eta=None)
    repo = FakeRepository([batch])
    session = FakeSession()

    allocate(line, repo, session)
    assert session.committed is True

def test_deallocate_decrements_available_quantity():
    line = OrderLine(ORDER_1, REAL_SKU, LOW_NUM)
    batch = Batch(BATCH_1, REAL_SKU, HIGH_NUM, None)
    repo, session = FakeRepository([batch]), FakeSession()
    batch_ref = allocate(line, repo, session)
    assert batch.available_qty == HIGH_NUM - LOW_NUM
    deallocate(line, batch_ref, repo, session)
    assert batch.available_qty == HIGH_NUM