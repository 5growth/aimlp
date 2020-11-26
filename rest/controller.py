from datetime import datetime
from model import *
from flask import Response, abort
from config import app, fs
from rest.training import run_training_algorithm
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
    # 403 Forbidden: training of not external models is not implemented yet
    if not model.external:
        app.logger.error("Training of internal models is not supported yet")
        abort(403)
    if model.status == ModelStatus.trained:
        app.logger.warning("Model training has been required for an already trained model")
    if model.status == ModelStatus.training:
        app.logger.error("Model training has been required for a model that is currently being trained")
        abort(403)
    model.status = ModelStatus.training
    db.session.commit()
    # TODO discuss/implement points 1,2,3,5
    engine = db.get_engine()
    training_thread = threading.Thread(target=run_training_algorithm,
                                       args=(engine, model_id),
                                       kwargs={"timeout": 600})
    training_thread.start()
    return model


def get_model_file(model_id):
    model = Model.query.get_or_404(model_id)

    # 403 Forbidden / 404 Not Found: cannot complete the request due to the file being unavailable
    if not model.status == ModelStatus.trained:
        abort(404)

    # for each model, the model file is located in <MODELS_DIR>/<id>/<file_name>
    file_dir = os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_MODELS_DIR"])
    file_name = str(model_id) + "_trained_model.zip"
    file_path = os.path.join(file_dir, file_name)
    # 503 Service unavailable: model file should be available but cannot be found in HDFS
    if not fs.exists(file_path):
        abort(503)
    else:
        return fs.open(file_path), model.download_file_name
