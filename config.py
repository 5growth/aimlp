import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import pyarrow as pa

app = Flask("AIML Platform")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///model_register.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JSON_SORT_KEYS"] = False
app.config["HDFS_ROOT_DIR"] = "/user/cpuligheddu/aiml_platform/model_files/"
os.environ['ARROW_LIBHDFS_DIR'] = '/opt/cloudera/parcels/CDH/lib/'

db = SQLAlchemy(app)
ma = Marshmallow(app)

try:
    fs = pa.hdfs.connect()
except pa.lib.ArrowIOError as e:
    app.logger.warning(str(e) + ". HDFS not available.")
    # define fs as an object with method "exists", which returns false,
    # in order to correctly handle the fs.exists call when HDFS isn't available
    fs = type("fsHandler", (object,), {"exists": lambda self: False})
