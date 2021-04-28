from datetime import datetime
from model import *
from flask import Response, abort
from config import app, fs
from rest.training import run_training_algorithm
import os.path
import threading
from rest.kafka_connector_manager import start_streaming, stop_streaming, process_metrics, get_dataset_dict_from_nsd

# This function will do the following:
# 0. check if the model is trainable or not
# 1. make sure that the training dataset is available before launching the training
# 2. retrieve optional parameters to be forwarded to the training algorithm
# 3. start the spark-submit process
# 4. move/compress the model binary in the proper directory
def start_training(model_id):
    model = Model.query.get_or_404(model_id)
    if model.status == ModelStatus.trained:
        app.logger.warning("Model training has been required for an already trained model")
    if model.status == ModelStatus.training:
        app.logger.error("Model training has been required for a model that is currently being trained")
        abort(403)
    model.status = ModelStatus.training
    db.session.commit()
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
        model.status = ModelStatus.error
        abort(503)
    else:
        return fs.open(file_path), model.download_file_name


def put_data_collector(collector):
    active_collector = DatasetCollector(kafka_topic=collector["kafka_topic"],
                                        kafka_server=collector["kafka_server"],
                                        nsd_id=collector["nsd_id"],
                                        status=CollectorStatus.started)
    try:
        metric_query, il_query = start_streaming(kafka_topic=active_collector.kafka_topic,
                                             kafka_server=active_collector.kafka_server,
                                             nsd_id=active_collector.nsd_id)
        active_collector.metric_query_id = metric_query
        active_collector.il_query_id = il_query
    except Exception as e:
        app.logger.warning(e)
        active_collector.status = CollectorStatus.error
    finally:
        db.session.add(active_collector)
        db.session.commit()
    return active_collector


def delete_data_collector(collector):
    if collector.status == CollectorStatus.started:
        collector.status = CollectorStatus.processing
        stop_streaming(collector.metric_query_id, collector.il_query_id)
        db.session.commit()

        engine = db.get_engine()
        processing_thread = threading.Thread(target=process_metrics,
                                             args=(engine, collector.collector_id),
                                             kwargs={"timeout": 1200})
        processing_thread.start()

    elif collector.status == CollectorStatus.terminated:
        # the collector is not started, therefore cannot be terminated
        abort(410)
    return collector


def get_dataset_file(nsd_id):
    collector = DatasetCollector.query.filter_by(nsd_id=nsd_id).filter_by(status=CollectorStatus.terminated).first()
    if collector is None:
        abort(404)
    return get_dataset_dict_from_nsd(nsd_id)