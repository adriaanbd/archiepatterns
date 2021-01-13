class SQLAlchemyUnitOfWork:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        pass

    def __exit__(self):
        pass