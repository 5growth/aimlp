import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from utils import dummy_fs
try:
    import pyarrow as pa
except ImportError:
    pass

app = Flask("AIML Platform")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///model_register.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["HDFS_ROOT_DIR"] = "/user/cpuligheddu/aiml_platform/model_files/"
os.environ['ARROW_LIBHDFS_DIR'] = '/opt/cloudera/parcels/CDH/lib/'

db = SQLAlchemy(app)
ma = Marshmallow(app)

try:
    fs = pa.hdfs.connect()
except NameError as e:
    app.logger.warning("Pyarrow not found. HDFS not available")
    fs = dummy_fs()
except pa.lib.ArrowIOError as e:
    app.logger.warning(str(e) + ". HDFS not available.")
    fs = dummy_fs()
