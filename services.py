import model
from repository import AbstractRepository
from typing import List


class InvalidSKU(Exception):
	pass

class UnallocatedSKU(Exception):
	pass


def is_valid_sku(line: model.OrderLine, batches: List[model.Batch]) -> bool:
	"""
	Validates an OrderLine's SKU against a list of Batches' SKU.
	"""
	skus = {b.sku for b in batches}
	return line.sku in skus

def allocate(line: model.OrderLine, repo: AbstractRepository, session) -> str:
	"""
	Obtains a list of Batches from data layer, validates OrderLine,
	calls the allocate domain service, and commits to database.
	"""
	batches = repo.list()
	if not is_valid_sku(line, batches):
		raise InvalidSKU(f'Invalid SKU: {line.sku}')
	ref = model.allocate(line, batches)
	session.commit()
	return ref

def add_batch(batch: model.Batch, repo: AbstractRepository, session):
	repo.add(batch)
	session.commit()

def is_allocated_sku(line, batch):
	return batch.has_been_allocated(line)

def deallocate(line: model.OrderLine, ref: str, repo: AbstractRepository, session):
	batch: model.Batch = repo.get(ref)
	if not is_allocated_sku(line, batch):
		raise UnallocatedSKU(f'Unallocated SKU: {line.sku}')
	batch.deallocate(line)
	session.commit()