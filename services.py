import model

def allocate(line, repo):
	batches = repo.list()
	ref = model.allocate(line, batches)
	return ref