from typing import Any, Generator

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Row
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.sql import text

__all__ = ["Record", "Result", "QuickSQL"]


class Record:
    """Represent a record queried from the database."""

    def __init__(self, record: Row) -> None:
        self.__record: Row = record

    def __contains__(self, item: Any) -> bool:
        return item in self.__record._mapping

    def __getattr__(self, name: str) -> Any:
        try:
            return getattr(self.__record, name)
        except AttributeError:
            raise AttributeError(f"'Record' object has no attribute {name!r}") from None

    def __getitem__(self, key: int | str) -> Any:
        if isinstance(key, int):
            return self.__record[key]
        return getattr(self.__record, key)


class Result:
    """Wrapper class for a SQL query result."""

    def __init__(self, /, result: CursorResult) -> None:
        self._result: CursorResult = result

    def __iter__(self) -> Generator[Record, None, None]:
        """Iterate over all results from the query."""
        for r in self.all():
            yield r

    def all(self) -> list[Record]:
        """Fetch all results from the query."""
        return [Record(r) for r in self._result.all()]

    def first(self) -> Record | None:
        """Fetch the first result from the query."""
        return Record(r) if (r := self._result.first()) else None

    def one(self) -> Record | None:
        """Fetch the only result from the query."""
        return Record(r) if (r := self._result.one_or_none()) else None


class QuickSQL:
    """A quick way to run SQL in your Flask app."""

    def __init__(self, app: Flask | None = None, /) -> None:
        _db: SQLAlchemy | None = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask, /) -> None:
        if app is None or not isinstance(app, Flask):
            raise TypeError("Parameter 'app' must be an active Flask instance.")

        # Don't permit double extension registration
        if "quick_sql" in app.extensions:
            raise RuntimeError(
                "A 'QuickSQL' instance has already been registered on this Flask app."
                " Import and use that instance instead."
            )

        # Register ourselves
        app.extensions["quick_sql"] = self

        with app.app_context():
            app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        # Register a SQLAlchemy instance if we don't already have one
        if "sqlalchemy" not in app.extensions:
            self._db = SQLAlchemy()
            self._db.init_app(app)

        # Otherwise, use the existing instance
        else:
            self._db = app.extensions["sqlalchemy"]

    def query(self, sql, /, **kwargs) -> Result:
        """Execute a SQL query.

        The underlying database connection is closed upon on method return.
        """
        with self._db.engine.connect() as conn:
            return Result(conn.execute(statement=text(sql), parameters=kwargs))
