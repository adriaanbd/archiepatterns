from unit_of_work import AbstractUnitOfWork
import model
from typing import List, Optional


class InvalidSKU(Exception):
    pass


def is_valid_sku(sku: str, batches: List[model.Batch]) -> bool:
    """
    Validates an OrderLine's SKU against a list of Batches' SKU.
    """
    skus = {b.sku for b in batches}
    return sku in skus

def add_batch(ref: str, sku: str, qty: int, eta: Optional[str], uow):
    batch = model.Batch(ref, sku, qty, eta)
    with uow:
        uow.batches.add(batch)
        uow.commit()

def allocate(orderid:str, sku: str, qty: int, uow) -> str:
    """
    Obtains a list of Batches from data layer, validates OrderLine,
    calls the allocate domain service, and commits to database.
    """
    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(sku, batches):
            raise InvalidSKU(f'Invalid SKU: {sku}')
        ref = model.allocate(orderid, sku, qty, batches)
        uow.commit()
    return ref


def deallocate(orderid:str, sku: str, qty: int, ref: str, uow):
    with uow:
        batch: model.Batch = uow.batches.get(ref)
        batch.deallocate(orderid, sku, qty)
        uow.commit()

def reallocate(line: model.OrderLine, uow: AbstractUnitOfWork) -> str:
    with uow:
        batch = uow.batches.get(sku=line.sku)
        if batch is None:
            raise InvalidSKU(f'Invalid sky {line.sku}')
        batch.deallocate(line)  # if this fails we don't allocate
        allocate(line)  # if this fails we don't deallocate either
        uow.commit()

def change_batch_quantity(batchref, new_qty, uow):
    with uow:
        batch = uow.batches.get(ref=batchref)
        batch.change_purchased_quantity(new_qty)
        while batch.available_qty < 0:
            batch.deallocate_one()
        uow.commit()