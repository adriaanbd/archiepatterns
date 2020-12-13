from model import OrderLine

ORDER_1 = "order1"
ORDER_2 = "order2"
CHAIR = "CHAIR"
TABLE = "TABLE"
LIPSTICK = "LIPSTICK"
WIDGET = 'WIDGET'
QUANTITY = 12
TWELVE, THIRTEEN, FOURTEEN = 12, 13, 14

# session param comes from './conftest.py'
def test_orderline_mapper_can_load_lines(session):
    session.execute(
        'INSERT INTO order_lines (orderid, sku, qty) VALUES '
        f'("{ORDER_1}", "{CHAIR}", "{QUANTITY}"),'
        f'("{ORDER_1}", "{TABLE}", "{QUANTITY + 1}"),'
        f'("{ORDER_2}", "{LIPSTICK}, "{QUANTITY + 2}")'
    )
    expected = [
        OrderLine(ORDER_1, CHAIR, TWELVE),
        OrderLine(ORDER_1, TABLE, THIRTEEN),
        OrderLine(ORDER_2, LIPSTICK, FOURTEEN)
    ]
    assert session.query(OrderLine).all() == expected

def test_orderline_mapper_can_save_lines(session):
    new_line = OrderLine(ORDER_1, WIDGET, TWELVE)
    session.add(new_line)
    session.commit()
    rows = list(
        session.execute(
            'SELECT orderid, sku, qty FROM "order_lines"'))
    assert rows == [(ORDER_1, WIDGET, TWELVE)]
