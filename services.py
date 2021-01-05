import model
from repository import AbstractRepository
from typing import List, Optional


class InvalidSKU(Exception):
    pass


def is_valid_sku(sku: str, batches: List[model.Batch]) -> bool:
    """
    Validates an OrderLine's SKU against a list of Batches' SKU.
    """
    skus = {b.sku for b in batches}
    return sku in skus

def add_batch(ref: str, sku: str, qty: int, eta: Optional[str], repo: AbstractRepository, session):
    batch = model.Batch(ref, sku, qty, eta)
    repo.add(batch)
    session.commit()

def allocate(orderid:str, sku: str, qty: int, repo: AbstractRepository, session) -> str:
    """
    Obtains a list of Batches from data layer, validates OrderLine,
    calls the allocate domain service, and commits to database.
    """
    batches = repo.list()
    if not is_valid_sku(sku, batches):
        raise InvalidSKU(f'Invalid SKU: {sku}')
    ref = model.allocate(orderid, sku, qty, batches)
    session.commit()
    return ref


def deallocate(orderid:str, sku: str, qty: int, ref: str, repo: AbstractRepository, session):
    batch: model.Batch = repo.get(ref)
    batch.deallocate(orderid, sku, qty)
    session.commit()