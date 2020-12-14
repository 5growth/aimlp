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
    from model import Model, Dataset, ServiceType, Scope, TrainingAlgorithm, ModelMlEngine
    from config import db, app, fs

    if forced:
        app.logger.warning("The database has been reset totally to default")
        db.drop_all()
        db.create_all()
    else:
        app.logger.warning("The Model and Dataset tables have been reset to default")
        Model.__table__.drop(db.engine)
        Dataset.__table__.drop(db.engine)
        Model.__table__.create(db.engine)
        Dataset.__table__.create(db.engine)


    dummy_algo = TrainingAlgorithm()

    db.session.add_all([dummy_algo])
    db.session.commit()

    model_files_dir = os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_MODELS_DIR"])
    not_trained_model_files_dir = os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_NOT_TRAINED_MODELS_DIR"])
    fs.delete(model_files_dir, recursive=True)
    fs.delete(not_trained_model_files_dir, recursive=True)
    fs.mkdir(model_files_dir)
    fs.mkdir(not_trained_model_files_dir)
    app.logger.warning("HDSF trained and not trained model directories have been emptied")


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
