from allocation.service_layer import unit_of_work
from allocation.domain import model
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
        product = uow.products.get(sku)
        if product is None:
            product = model.Product(sku, batches=[])
            uow.products.add(product)
        product.batches.append(batch)
        uow.commit()

def allocate(orderid:str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork) -> str:
    """
    Obtains a list of Batches from data layer, validates OrderLine,
    calls the allocate domain service, and commits to database.
    """
    with uow:
        product = uow.products.get(sku)
        if product is None:
            raise InvalidSKU(f'Invalid SKU: {sku}')
        ref = product.allocate(orderid, sku, qty)
        uow.commit()
    return ref


def deallocate(orderid:str, sku: str, qty: int, ref: str, uow):
    with uow:
        batch: model.Batch = uow.batches.get(ref)
        batch.deallocate(orderid, sku, qty)
        uow.commit()

def reallocate(line: model.OrderLine, uow: unit_of_work.AbstractUnitOfWork) -> str:
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