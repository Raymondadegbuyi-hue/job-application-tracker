from flask import Flask
from markupsafe import escape

app = Flask(__name__)


@app.route("/")
def home():
    return "<h1>Job Application Tracker</h1><p>Flask is working.</p>"


@app.route("/hello/<name>")
def hello(name):
    return f"<p>Hello, {escape(name)}!</p>"