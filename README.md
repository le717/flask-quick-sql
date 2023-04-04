# flask-quick-sql

> A quick way to run SQL in your Flask app.

## Info

A long time ago, I used the [`records`](https://pypi.org/project/records/) library to query a database with raw SQL. It was great, [until it wasn't](https://github.com/kennethreitz/records/issues/208).

Fast-forward many years and I was working on replacing the code that used `records`, but I needed to keep the existing code working. I also needed to remove `records` from my dependencies in order to update literally _everything_, but alas, I could not.

Enter this little wrapper code I wrote. It _kinda_ keeps API compat but also kinda not.
That wasn't my goal. My goal was to keep _enough_ compatibility so I wouldn't have to
change much of my code while also keeping it nice to use.

This Flask extension exists solely because I liked my wrapper code and will
almost certainly will have a use for it again, and I didn't want it to just go away
when I deleted it from my app.

## Usage

```python
from flask import Flask
from flask_quick_sql import QuickSQL


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = ...
    quick_sql = QuickSQL(app)

    all_users = quick_sql.query("SELECT * FROM users").all()
    print(all_users[0]["username"])

    return app
```

The immediate result of `query()` isn't very useful. You'll want to chain a call to `.all()`, `.first()`, or `.one()`.

You don't get property and key access like `records` gave you. You get one or the other. By default, you get a dictionary. Breaking API change from `records`? Yes, I don't care.

To get a `collections.namedtuple`, pass `as_nt=True` as a parameter to any method. Your type hints will break since you can't define a hint for dynamically created named tuples, but it's what's it's.

You can also iterate over the whole result set, with each record being `yield`ed:

```python
[User(r) for r in quick_sql.query("SELECT * FROM users")]
```

Because SQLAlchemy is used under the hood, prepared statements work as expected:

```python
sql = "SELECT * FROM users WHERE is_active = :is_active"
[User(r) for r in db.query(sql, is_active=False)]
```

Have fun running your [SQuirreL](http://www.squirrelsql.org/) queries.

## License

[Public domain](LICENSE)
