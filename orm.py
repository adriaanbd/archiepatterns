from sqlalchemy import (
    MetaData, Table, Column, Integer, String, Date, ForeignKey
)
from sqlalchemy.orm import mapper, relationship
from model import OrderLine, Batch

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
    Column('reference', String(255)),
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
    lines_mapper = mapper(OrderLine, order_lines)
    mapper(Batch, batches, properties={
        '_allocations': relationship(
            lines_mapper,
            secondary=allocations,
            collection_class=set,
        )
    })

