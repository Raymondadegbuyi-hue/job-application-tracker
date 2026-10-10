import sqlite3

import click
from flask import current_app, g


def get_db():
    """Open one database connection per request and reuse it."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row  # lets us use row["company"] instead of row[1]
    return g.db


def close_db(error=None):
    """Close the connection when the request is finished."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the tables from schema.sql."""
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))


@click.command("init-db")
def init_db_command():
    """Terminal command: flask --app app init-db"""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    """Connect these functions to the Flask app."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
