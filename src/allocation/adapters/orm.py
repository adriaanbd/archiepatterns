from sqlalchemy import (
    MetaData, Table, Column, Integer, String, Date, ForeignKey
)
from sqlalchemy.orm import mapper, relationship
from allocation.domain import model

# https://docs.sqlalchemy.org/en/13/core/metadata.html#sqlalchemy.schema.MetaData
# Holds a collection of Table objects and optional binding to
# an Engine or Connection. Stored in MetaData.tables dictionary.
metadata = MetaData()

order_lines = Table(
    'order_lines', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('sku', String(255)),
    Column('qty', Integer, nullable=False),
    Column('orderid', String(255)),
)

batches = Table(
    'batches', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('ref', String(255)),
    Column('sku', String(255)),
    Column('_qty', Integer, nullable=False),
    Column('eta', Date, nullable=True),
)

allocations = Table(
    'allocations', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('orderline_id', ForeignKey('order_lines.id')),
    Column('batch_id', ForeignKey('batches.id')),
)

def start_mappers():
    lines_mapper = mapper(model.OrderLine, order_lines)  # returns Mapper object that defines correlation
    # of class attrs to ddbb table columns. When mapper() is used explicitly to link a user defined
    # class with table metadata, this is referred to as classical mapping.
    # https://docs.sqlalchemy.org/en/13/orm/mapping_api.html#sqlalchemy.orm.mapper.params.properties
    # https://docs.sqlalchemy.org/en/13/orm/relationship_api.html#sqlalchemy.orm.relationship
    mapper(model.Batch, batches, properties={
        '_allocations': relationship(
            lines_mapper,  # mapped class or Mapper instance representing relationship target
            secondary=allocations, # intermediary junction table to link two tables
            collection_class=set,  # will be used in place of default list() for storing elems
        )
    })

