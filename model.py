from dataclasses import dataclass
from typing import Optional
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
        self.qty = qty
        self.eta = eta

    def _can_allocate(self, line: OrderLine):
        return self.qty > line.qty

    def allocate(self, line: OrderLine):
        if self._can_allocate(line):
            self.qty -= line.qty
