from __future__ import annotations
from dataclasses import dataclass
from typing import NewType, Set, TypeVar, List
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
@dataclass(unsafe_hash=True)
class OrderLine:
    """
    Customers place orders. An order is identified by
    an order reference and comprises multiple order
    lines where each line has a SKU and a quantity.
    """
    orderid: OrderId
    sku: Sku
    qty: Qty


# Entities have identity equality. We can
# change their values and they are still
# the same.
class Batch:
    """
    The purchasing department orders small batches of
    stock. A batch of stock has a unique ID, a SKU, and
    a quantity.

    A class that represents a Batch of items

    Attributes:
        ref:
            The reference used for a Batch
        sku:
            Stock Keeping Unit
        eta:
            Estimated Time of Arrival
        qty:
            Quantity of items
        allocations:
            A set of Order Lines allocated to a Batch
    """
    def __init__(self, ref: Ref, sku: Sku, qty: Qty, eta: Eta = None) -> None:
        self.ref = ref
        self.sku = sku
        self.eta = eta
        self._qty = qty
        self._allocations: Set[OrderLine] = set()

    def allocate(self, line: OrderLine) -> None:
        """Allocates an OrderLine to a Batch

        Allocates an OrderLine to a Batch if the OrderLine's
        sku matches the Batch's sku and if the Batch's available
        quantity is greater or equal to the OrderLine's quantity.
        Idempotency is guaranteed by the the use of a set, which
        achieves uniqueness of a Batch by a hash of its reference
        attribute.

        Args:
            OrderLine
        """
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, orderid, sku, qty) -> None:
        line = OrderLine(orderid, sku, qty)
        if not self.has_been_allocated(line):
            raise UnallocatedSKU(f'Unallocated SKU: {sku}')
        self._allocations.remove(line)

    @property
    def allocated_qty(self) -> int:
        """Agregates the quantity of all allocated Order Lines

        A Batch must keep track of the total quantity of SKUs
        allocated to it.

        Returns:
            The quantity of all allocations
        """
        qty = sum(line.qty for line in self._allocations)
        return qty

    @property
    def available_qty(self) -> int:
        qty = self._qty - self.allocated_qty
        return qty

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_qty >= line.qty

    def has_been_allocated(self, line) -> bool:
        return line in self._allocations

    def __repr__(self):
        return f'<Batch {self.ref}>'

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

    def __gt__(self, other) -> bool:
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta


# a Domain Excepction
class OutOfStock(Exception):
    pass

class UnallocatedSKU(Exception):
    pass

# a Domain Service
def allocate(orderid: OrderId, sku: Sku, qty: Qty, batches: List[Batch]) -> str:
    """
    Domain Service to allocate order lines against a list of batches
    """
    assert len(batches) > 0, "At least 1 batch is needed"
    line = OrderLine(orderid, sku, qty)
    try:
        batch = next(
            b for b in sorted(batches)
            if b.can_allocate(line)
        )
        batch.allocate(line)
        return batch.ref
    except StopIteration:
        raise OutOfStock(f'Out of stock for {line.sku}')

