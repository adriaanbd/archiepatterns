# Domain Modeling

## Concepts

**Domain**: the problem you’re trying to solve.
  
**Model**: map of a process to capture a useful propery.

**Domain Model**: mental map that business owners have of their businesses.

## Question and Comments

1. A Batch has an instance attribute of `qty` that keeps the state of the
count of all items assigned to a Batch instance. However, the only
relevant quantity attribute from a business perspective is the
`available_qty`. In this sense, shouldn't the `qty` attribute be a private
and only used by the instance itself?

2. The `#allocate` domain service uses the `next()` as an approach to
   obtain the batch with the closes ETA from a list of batches if the
   batch can allocate the OrderLine passed in as an argument. 
