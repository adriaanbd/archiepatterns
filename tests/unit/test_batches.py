# THESE TESTS HAVE BEEN MOVED TO THE SERVICE LAYER TESTS

# from model import Batch, OrderLine

# QUANTITY, GREATER, SMALLER = 20, 30, 10
# SKU, BATCH_REF, ORDER_REF = 'CRAZY_LAMP', 'batch-ref', 'order-ref'

# def make_batch_n_line(sku, batch_qty, line_qty):
#     batch = Batch(BATCH_REF, sku, batch_qty, line_qty)
#     line = OrderLine(ORDER_REF, sku, line_qty)
#     return batch, line

# def test_does_allocate_if_available_greater_than_required():
#     batch, line = make_batch_n_line(SKU, QUANTITY, SMALLER)
#     batch.allocate(line)
#     assert batch.available_qty == QUANTITY - SMALLER

# def test_doesnt_allocate_if_available_smaller_than_required():
#     batch, line = make_batch_n_line(SKU, QUANTITY, GREATER)
#     batch.allocate(line)
#     assert batch.available_qty == QUANTITY

# def test_does_allocate_if_available_equal_to_required():
#     batch, line = make_batch_n_line(SKU, QUANTITY, QUANTITY)
#     batch.allocate(line)
#     assert batch.available_qty == 0

# def test_doesnt_allocate_if_skus_do_not_match():
#     batch = Batch(BATCH_REF, SKU, QUANTITY)
#     line = OrderLine(ORDER_REF, 'SANE_LAMP', SMALLER)
#     batch.allocate(line)
#     assert batch.available_qty == QUANTITY

# def test_can_only_deallocate_allocated_lines():
#     batch, unallocated_line = make_batch_n_line(SKU, QUANTITY, SMALLER)
#     batch.deallocate(unallocated_line)
#     assert batch.available_qty == QUANTITY

# def test_allocation_is_idempotent():
#     batch, line = make_batch_n_line(SKU, QUANTITY, SMALLER)
#     batch.allocate(line)
#     batch.allocate(line)
#     assert batch.available_qty == QUANTITY - SMALLER