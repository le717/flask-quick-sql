from typing import Any, Generator

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Row
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.sql import text


__all__ = ["Result", "QuickSQL"]


class Result:
    """Wrapper class for a SQL query result."""

    def __init__(self, /, result: CursorResult) -> None:
        self._result: CursorResult = result

    def __iter__(self) -> Generator[dict[str, Any], None, None]:
        """Iterate over all results from the query."""
        for r in self.all():
            yield r

    def all(self, *, as_nt: bool = False) -> list[dict[str, Any]] | list[Row]:
        """Fetch all results from the query."""
        return [r if as_nt else r._asdict() for r in self._result.all()]

    def first(self, *, as_nt: bool = False) -> dict[str, Any] | Row | None:
        """Fetch the first result from the query."""
        # Specifically handle no results
        if (r := self._result.first()) is None:
            return None
        return r if as_nt else r._asdict()

    def one(self, *, as_nt: bool = False) -> dict[str, Any] | Row | None:
        """Fetch the only result from the query."""
        # Specifically handle no results
        if (r := self._result.one_or_none()) is None:
            return None
        return r if as_nt else r._asdict()


class QuickSQL:
    """A quick way to run SQL in your Flask app."""

    def __init__(self, app: Flask | None = None, /) -> "QuickSQL":
        _db: SQLAlchemy = None

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
