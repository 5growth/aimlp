from datetime import datetime
from model import *
from flask import Response, abort
from config import app, fs
from rest.training import train_model
import os.path
import threading


# This function will do the following:
# 0. check if the model is trainable or not
# 1. check that training algorithm requirements (needed python packages) are available in the YARN cluster workers
# 2. make sure that the training dataset is available before launching the training
# 3. retrieve optional parameters to be forwarded to the training algorithm
# 4. start the spark-submit process
# 5. move/compress the model binary in the proper directory
def start_training(model_id):
    model = Model.query.get_or_404(model_id)
    # 403 Forbidden: training of not trainable models is not possible
    if not model.trainable:
        abort(403)

    # TODO discuss/implement points 1,2,3,5
    engine = db.get_engine()
    training_thread = threading.Thread(target=train_model,
                                       args=(engine, model_id),
                                       kwargs={"timeout": 600})
    training_thread.start()

    model.status = ModelStatus.training
    model.latest_update = datetime.utcnow()
    db.session.commit()
    return model


def get_model_file(model_id):
    model = Model.query.get_or_404(model_id)

    # 403 Forbidden: cannot complete the request due to the file being unavailable
    if not model.validity:
        abort(403)

    # for each model, the model file is located in <MODELS_DIR>/<id>/<file_name>
    file_path = os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_MODELS_DIR"], model_id, model.file_name)
    # 503 Service unavailable: model file should be available but cannot be found in HDFS
    if not fs.exists(file_path):
        abort(503)
    else:
        return fs.open(file_path), model.file_name
