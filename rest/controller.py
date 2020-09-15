from datetime import datetime
from model import *
from flask import Response, abort
from config import app, fs
import os.path


def start_training(model_id):
    model = Model.query.get_or_404(model_id)
    model.latest_update = datetime.utcnow()
    model.status = ModelStatus.training
    # TODO launch training

    db.session.commit()
    return model


def get_model_file(model_id):
    model = Model.query.get_or_404(model_id)

    # 409 Conflict: cannot complete the request due to a conflict
    # with the current state of the resource (currently invalid model)
    if not model.validity:
        abort(409)

    # for each model, the model file is located in /id/file_name
    file_path = os.path.join(app.config["HDFS_ROOT_DIR"], model_id, model.file_name)
    if not fs.exists(file_path):
        abort(404)
    else:
        return fs.open(file_path), model.file_name
