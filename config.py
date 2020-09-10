from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask("AIML Platform")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///model_register.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JSON_SORT_KEYS"] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)
