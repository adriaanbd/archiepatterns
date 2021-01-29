from abc import ABC, abstractmethod
from allocation.domain import model

class AbstractRepository(ABC):

    @abstractmethod
    def add(self, products: model.Product):
        raise NotImplementedError

    @abstractmethod
    def get(self, sku) -> model.Product:
        raise NotImplementedError

class SQLAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def add(self, batch):
        # https://docs.sqlalchemy.org/en/13/orm/session_api.html#sqlalchemy.orm.session.Session.add
        self.session.add(batch)  # places batch in the Session, its state will be persisted to the
        # ddbb on the next flush operation

    def get(self, reference):
        return self.session.query(model.Batch).filter_by(
            ref=reference).one()

    def list(self):
        return self.session.query(model.Batch).all()

