from dataclasses import dataclass
from typing import NewType, Optional, Set, TypeVar
from datetime import date

Qty = NewType('Qty', int)
Sku = NewType('Sku', str)
Ref = NewType('Ref', str)
OrderId = NewType('OrderId', str)
Eta = TypeVar('Eta', date, None)


# A ValueObject is uniquely identified
# by the data it holds. It's usually
# immutable. Dataclasses gives us value
# equality. Two lines with the same
# orderid, sky and qty are equal
@dataclass(frozen=True)
class OrderLine: 
    orderid: OrderId
    sku: Sku
    qty: Qty


# Entities have identity equality. We can
# change their values and they are still
# the same. 
class Batch:
    def __init__(self, ref: Ref, sku: Sku, qty: Qty, eta: Eta = None) -> None:
        self.ref = ref
        self.sku = sku
        self.eta = eta
        self.qty = qty
        self._allocations: Set[OrderLine] = set()

    def allocate(self, line: OrderLine) -> None:
        if self._can_allocate(line):
            self._allocations.add(line)
    
    def deallocate(self, line: OrderLine) -> None:
        if self._has_been_allocated(line):
            self._allocations.remove(line)

    @property
    def allocated_qty(self) -> int:
        qty = sum(line.qty for line in self._allocations)
        return qty

    @property
    def available_qty(self) -> int:
        qty = self.qty - self.allocated_qty
        return qty

    def _has_been_allocated(self, line) -> bool:
        return line in self._allocations

    def _can_allocate(self, line: OrderLine) -> bool:
        return self.qty >= line.qty and self.sku == line.sku
    
    # Enforce identity equality on ref
    def __eq__(self, other) -> bool:
        if not isinstance(other, Batch):
            return False
        return other.ref == self.ref
    
    # make Batch hashable to use in dict or set
    # two instances of Batch will have diff hashes
    # the hash must never change during its lifetime
    # has to be defined with __eq__, same eq same hash
    # see: https://hynek.me/articles/hashes-and-equality/
    def __hash__(self) -> int:
        return hash(self.ref)