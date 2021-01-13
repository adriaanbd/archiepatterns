from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime

import config
import model
import orm
import repository
import services


orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)

@app.route("/allocate", methods=['POST'])
def allocate_endpoint():
    session = get_session()
    repo = repository.SQLAlchemyRepository(session)
    oid, sku, qty = (
        request.json['orderid'],
        request.json['sku'],
        request.json['qty'],
    )
    try:
        batchref = services.allocate(oid, sku, qty, repo, session)
    except (
        model.OutOfStock,
        model.UnallocatedSKU,
        services.InvalidSKU
    ) as exc:
        return jsonify({'message': str(exc)}), 400

    return jsonify({'batchref': batchref}), 201


@app.route("/add_batch", methods=['POST'])
def add_batch():
    session = get_session()
    repo = repository.SQLAlchemyRepository(session)
    eta = request.json['eta']
    if eta is not None:
        eta = datetime.date.fromisoformat(eta)
    r, s, q = request.json['ref'], request.json['sku'], request.json['qty']
    services.add_batch(r, s, q, eta, repo, session)

    return 'OK', 201