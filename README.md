# The Repository Pattern

## Ideas

1. The **Repository** pattern is an abstraction over data storage.
2. This pattern allows to decouple the *model* layer from the *data* layer.
3. It makes the system more testable by hiding complexities of the database.
4. It sits between the domain model and the database.
5. Its an application of the dependency inversion principle: high-level modules (the domain) should not
depend on low-level ones (the infrastructure).
6. It hides all the details of data access by *pretending* that all our data is *in memory*.
7. A Repository is, in Python, any object that has the `add(thing)`
and `get(id)` methods.

## Reasoning

The domain model should have no *stateful dependencies* (helper library is fine; an ORM or web
framework is not).

The domain model should not have any infrastructure concerns because:
* it slows down unit tests
* hinders ability to make changes

It allows for dependencies to flow inward into the domain model that sits at the center (onion architecture).

Figure:

Presentation Layer => Domain Model <= Database Layer

## The Normal ORM way

Usually, an Object Relational Mapper (ORM) is used to generate SQL based on model objects.
An ORM provides *persistence ignorance*: the idea that the domain model doesn't
know anything about how data is loaded or persisted.

The typical SQLAlchemy snippet:

```python
# the import statements omitted

class Order(Base):
    id = Column(Integer, primary_key=True)

class OrderLine(Base):
    id = Column(Integer, primary_key=True)
    sku = Column(String(250))
    # ... the rest omitted

class Allocation(Base):
    pass
```

The typical Django ORM snippet:

```python
class Order(models.Model):
    pass

class OrderLine(models.Model):
    sku = models.CharField(max_length=255)
    qty = models.IntegerField()
    # ... rest omitted

class Allocation(models.Model):
    pass
```

## Inverting the Dependency

The schema can be defined separately.
A mapper can be used to convert between the schema and the domain model.
SQLAlchemy calls this a [classical
mapping](https://docs.sqlalchemy.org/en/13/orm/mapping_styles.html#classical-mappings)

### Implications

If we just invert the dependency, the Flask API endpoint might look like this:

```python
@flask.route.gubbins
def allocate_endpoint():
    session = start_session()
    orderid = request.json['orderid']
    sku = request.json['sku']
    qty = request.json['qty']
    line = OrderLine(orderid, sku, qty)
    batches = session.query(Batch).all()
    allocate(line, batches)
    session.commit()
    return 201
```

If we take it a step further and implement the Repository pattern as an abstraction over data persistence then this endpoint might look like this:

```python
@flask.route.gubbins
def allocate_endpoint():
    batches = SQLAlchemyRepository.list()
    lines = [
	OrderLine(l['orderid'], l['sku'], l['qty'])
	for l in request.params
    ]
    allocate(lines, batches)
    session.commit()
    return 201
```

## Benefit

It allows us to easily load and save domain model instance from and to the database. However, if we never call that function, our domain model classes stay unaware of the database. This provides us with the benefits of using SQLAlchemy and its ecosystem of libraries, i.e. *alembic* for migrations, and the ability to query the the database using our domain classes.

Furthermore, we can:
* throw away SQLAlchemy and use a different ORM
* use a different persistence system
* the domain model doesn't need to change if we do the above

*Note*: consider the tradeoff of specific architectural decisions.

## Approach to the DIP

When building the ORM config, it's useful to write tests for it.

For example:
1. The orderline mapper can load data into the database.
2. The orderline mapper can persist data to the database.

## Trade-Offs

Pros:

1. Simple interface between persistent storage and domain model
2. Easier to make fake version of repository for unit testing.
3. Easier to swap out different storage solutions
4. Writing the domain model before thinking about persistence helps to focus on the business problem at hand. This allows us to radically change our approach without needing to worry about foreign keys or migrations until later.
5. The database schema is really simple because we have complete control over how we map objects to tables.

Cons:

1. An ORM already buys some deocupling. Changing foreign keys might be hard but it should be
   easy to swap between MySQL and Postgres.
2. Maintaining ORM mappings by hand requires extra work and extra code.
3. Any extra layer of indirection always increases maintenance costs.

## Comments

1. If the app is just a simple CRUD wrapper around a database, then no domain model or repository pattern is needed.
2. The more complex the domain, the more an investment in freeing yourself from infrastructure concerns will pay off.

## Recap

1. Apply DIP to your ORM.
2. Repository pattern is an abstraction around permanent storage.
