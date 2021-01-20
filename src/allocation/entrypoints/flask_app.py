from flask import Flask, jsonify, request
import datetime

from allocation.domain import model
from allocation.adapters import orm
from allocation.service_layer import services, unit_of_work


app = Flask(__name__)
orm.start_mappers()

@app.route("/allocate", methods=['POST'])
def allocate_endpoint():
    uow = unit_of_work.SQLAlchemyUnitOfWork()

    oid, sku, qty = (
        request.json['orderid'],
        request.json['sku'],
        request.json['qty'],
    )
    try:
        batchref = services.allocate(oid, sku, qty, uow)
    except (
        model.OutOfStock,
        model.UnallocatedSKU,
        services.InvalidSKU
    ) as exc:
        return jsonify({'message': str(exc)}), 400

    return jsonify({'batchref': batchref}), 201


@app.route("/add_batch", methods=['POST'])
def add_batch():
    uow = unit_of_work.SQLAlchemyUnitOfWork()

    eta = request.json['eta']
    if eta is not None:
        eta = datetime.date.fromisoformat(eta)
    r, s, q = request.json['ref'], request.json['sku'], request.json['qty']
    services.add_batch(r, s, q, eta, uow)

    return 'OK', 201