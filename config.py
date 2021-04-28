import os
from pyspark.sql import SparkSession
import subprocess
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_login import LoginManager
from rest.utils import dummy_fs, init_started_collectors
from pathlib import Path

try:
    import pyarrow as pa
except ImportError:
    pass

# Start anc configure the basic Flask application
app = Flask("AIML Platform", template_folder="web/templates/")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "secret-key-goes-here"
# HDFS Namenode URI, as reported in core-site.xml
app.config["HDFS_NAMENODE"] = "hdfs://master.awe.polito.it:8020"
app.config["LOCAL_HDFS_DIR"] = str(Path.home().joinpath('hdfs'))
app.config["HDFS_ROOT_DIR"] = "/user/worker/"
app.config["HDFS_MODELS_DIR"] = "model_files/"
app.config["HDFS_NOT_TRAINED_MODELS_DIR"] = "not_trained_model_files/"
app.config["HDFS_METRICS_DIR"] = "metrics/"
os.environ["ARROW_LIBHDFS_DIR"] = "/opt/cloudera/parcels/CDH/lib/"
os.environ["HADOOP_HOME"] = "/opt/cloudera/parcels/CDH/lib/hadoop/"
# os.environ["CLASSPATH"] = ":" + subprocess.run(["hdfs", "classpath", "--glob"],
#                                           capture_output=True,
#                                           text=True).stdout.strip()
os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-8-oracle-cloudera/"
#os.environ["HADOOP_CONF_DIR"] = "/opt/cloudera/parcels/CDH-6.3.2-1.cdh6.3.2.p0.1605554/lib/spark/conf/yarn-conf:/etc/hive/conf"
# print(os.environ["CLASSPATH"])

# set rest-spark-submit.sh execution permissions
os.chmod("./rest-spark-submit.sh", 0o764)
os.chmod("./rest-spark-submit_light.sh", 0o764)
 # Attach SQLAlchemy and Marshmallow to the Flask app
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Load, attach and configure the login manager
login_manager = LoginManager()
login_manager.login_view = 'web.auth.login'
login_manager.init_app(app)


# Establish a connection to HDFS. Set a dummy fs object in case of issues
try:
    fs = pa.hdfs.connect()
except NameError as e:
    app.logger.warning("Pyarrow package not found. HDFS not available")
    fs = dummy_fs()
except pa.lib.ArrowIOError as e:
    app.logger.warning(str(e) + ". HDFS not available.")
    fs = dummy_fs()

# Mount HDFS as local file system
if not os.path.ismount(app.config["LOCAL_HDFS_DIR"]):
    app.logger.info("HDFS is not accessible as local file system. Mounting now...")
    try:
        mount_cmd = subprocess.run(
            ["hadoop-fuse-dfs", "-oprivate", app.config["HDFS_NAMENODE"], app.config["LOCAL_HDFS_DIR"]],
            capture_output=True,
            text=True)
        if mount_cmd.returncode == 0 and os.path.ismount(app.config["LOCAL_HDFS_DIR"]):
            app.logger.info("HDFS successfully mounted as local file system")
        else:
            app.logger.error("FUSE error")
            app.logger.error(mount_cmd.stderr)
            app.logger.error(mount_cmd.stdout)
    except FileNotFoundError as e:
        app.logger.warning(str(e) + ". HDFS could not be mounted as local file system")
else:
    app.logger.info("HDFS is already accessible as local file system")

# start a Spark Session
spark = SparkSession.builder.master("local[1]").appName("AIML-kafka-connector") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.0") \
    .getOrCreate()


# blueprint for auth routes in our app
from web.auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

# blueprint for non-auth parts of app
from web.main import main as main_blueprint
app.register_blueprint(main_blueprint)

init_started_collectors()