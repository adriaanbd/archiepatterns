import model


class InvalidSKU(Exception):
	pass


def is_valid_sku(line, batches):
	skus = {b.sku for b in batches}
	return line.sku in skus

def allocate(line, repo, session):
	batches = repo.list()
	if not is_valid_sku(line, batches):
		raise InvalidSKU(f'Invalid SKU: {line.sku}')
	ref = model.allocate(line, batches)
	session.commit()
	return ref