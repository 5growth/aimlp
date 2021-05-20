from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from marshmallow.validate import OneOf
from marshmallow import fields
from zipfile import ZipFile
import os


# Define fs as an object with method "exists", which returns false,
# in order to correctly handle the fs.exists call when HDFS isn't available
def dummy_fs():
    return type("fsHandler", (object,), {"exists": lambda self: False})


def get_scoped_session(engine):
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)


def reset_db(forced=False):
    from model import Model, Dataset, ServiceType, Scope, TrainingAlgorithm, ModelMlEngine, DatasetCollector
    from config import db, app, fs

    if forced:
        app.logger.warning("The database has been reset totally to default")
        db.drop_all()
        db.create_all()
    else:
        app.logger.warning("The Model, Dataset and Collector tables have been reset to default")
        Model.__table__.drop(db.engine)
        Dataset.__table__.drop(db.engine)
        DatasetCollector.__table__.drop(db.engine)
        Model.__table__.create(db.engine)
        Dataset.__table__.create(db.engine)
        DatasetCollector.__table__.create(db.engine)

    dummy_algo = TrainingAlgorithm()

    db.session.add_all([dummy_algo])
    db.session.commit()

    model_files_dir = os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_MODELS_DIR"])
    not_trained_model_files_dir = os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_NOT_TRAINED_MODELS_DIR"])
    metrics_dir = os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_METRICS_DIR"])
    hdfs_dirs = [model_files_dir, not_trained_model_files_dir, metrics_dir]
    for d in hdfs_dirs:
        fs.delete(d, recursive=True)
        fs.mkdir(d)
    app.logger.warning("HDFS trained and not trained model directories have been emptied")


def EnumField(enum_class):
    return fields.Field(validate=[OneOf(choices=[e.value for e in enum_class])])


def zip_dir(path, zip_h):
    # path has to be local fs, cannot be HDFS
    for root, dirs, files in os.walk(path):
        for file in files:
            zip_h.write(os.path.join(root, file), arcname=os.path.relpath(os.path.join(root, file), path))


def zip_externally_trained_model_files(engine, model_id):
    from model import Model, ModelStatus
    from config import fs, app

    Session = get_scoped_session(engine)
    session = Session()
    model = session.query(Model).get(model_id)
    model_folder = os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_MODELS_DIR"])
    model_id_folder = os.path.join(app.config["LOCAL_HDFS_DIR"] + app.config["HDFS_ROOT_DIR"],
                                   app.config["HDFS_MODELS_DIR"], str(model_id))
    zip_fd = fs.open(os.path.join(model_folder, str(model_id) + "_trained_model.zip"), mode='wb')
    zip_h = ZipFile(zip_fd, "w")
    zip_dir(model_id_folder, zip_h)
    zip_h.close()
    zip_fd.close()
    model.status = ModelStatus.trained
    session.commit()
    Session.remove()


def init_started_collectors():
    from model import DatasetCollector, CollectorStatus
    from config import app, db
    if not db.engine.dialect.has_table(db.engine, DatasetCollector.__tablename__):
        app.logger.warning("Dataset collector table not found in the DB. A DB reset may be required")
        return
    error_collectors = DatasetCollector.query.filter_by(status=CollectorStatus.error).all()
    for c in error_collectors:
        db.session.delete(c)
    started_collectors = DatasetCollector.query.filter(DatasetCollector.status != CollectorStatus.terminated).all()
    for c in started_collectors:
        c.status = CollectorStatus.error
    db.session.commit()
    dirty_count = len(error_collectors) + len(started_collectors)
    if dirty_count > 0:
        app.logger.warning(str(dirty_count) + " not terminated collectors were found during startup.")
