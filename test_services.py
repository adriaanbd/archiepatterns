from repository import AbstractRepository
from model import OrderLine, Batch
from services import allocate


class FakeRepository(AbstractRepository):

    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.ref == reference)

    def list(self):
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

    result = allocate(line, repo)
    assert result == BATCH_1
