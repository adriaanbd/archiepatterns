from dataclasses import dataclass
from typing import Optional, Set
from datetime import date


@dataclass(frozen=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


class Batch:
    def __init__(
        self, ref: str, sku: str, qty: int, eta: Optional[date] = None):
        self.ref = ref
        self.sku = sku
        self.eta = eta
        self.qty = qty
        self._allocations: Set[OrderLine] = set()

    def allocate(self, line: OrderLine):
        if self._can_allocate(line):
            self._allocations.add(line)
    
    def deallocate(self, line: OrderLine):
        allocated = line in self._allocations
        if allocated:
            self._allocations.remove(line)

    @property
    def allocated_qty(self):
        qty = sum(line.qty for line in self._allocations)
        return qty

    @property
    def available_qty(self):
        qty = self.qty - self.allocated_qty
        return qty

    def _can_allocate(self, line: OrderLine):
        return self.qty >= line.qty and self.sku == line.sku