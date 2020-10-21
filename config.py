import os
import subprocess
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_login import LoginManager
from rest.utils import dummy_fs
try:
    import pyarrow as pa
except ImportError:
    pass

# Start anc configure the basic Flask application
app = Flask("AIML Platform", template_folder="web/templates/")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "secret-key-goes-here"
app.config["HDFS_ROOT_DIR"] = "/user/worker/"
app.config["HDFS_MODELS_DIR"] = "model_files/"
os.environ["ARROW_LIBHDFS_DIR"] = "/opt/cloudera/parcels/CDH/lib/"
os.environ["HADOOP_HOME"] = "/opt/cloudera/parcels/CDH/lib/hadoop/"
os.environ["CLASSPATH"] = ":" + subprocess.run(["hdfs", "classpath", "--glob"],
                                          capture_output=True,
                                          text=True).stdout.strip()
os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-8-oracle-cloudera/"
# print(os.environ["CLASSPATH"])

# Attach SQLAlchemy and Marshmallow to the Flask app
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Load, attach and configure the login manager
login_manager = LoginManager()
login_manager.login_view = 'web.auth.login'
login_manager.init_app(app)

# blueprint for auth routes in our app
from web.auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

# blueprint for non-auth parts of app
from web.main import main as main_blueprint
app.register_blueprint(main_blueprint)

# Establish a connection to HDFS. Set a dummy fs object in case of issues
try:
    fs = pa.hdfs.connect()
except NameError as e:
    app.logger.warning("Pyarrow package not found. HDFS not available")
    fs = dummy_fs()
except pa.lib.ArrowIOError as e:
    app.logger.warning(str(e) + ". HDFS not available.")
    fs = dummy_fs()
