import os

from flask import Flask
from markupsafe import escape

import db

app = Flask(__name__)

# Store the database file in the "instance" folder, which Git ignores
app.config["DATABASE"] = os.path.join(app.instance_path, "tracker.sqlite")
os.makedirs(app.instance_path, exist_ok=True)

db.init_app(app)


@app.route("/")
def home():
    count = db.get_db().execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    return f"<h1>Job Application Tracker</h1><p>Applications saved: {count}</p>"


@app.route("/hello/<name>")
def hello(name):
    return f"<p>Hello, {escape(name)}!</p>"
