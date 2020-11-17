import subprocess
from datetime import datetime
from model import Model, ModelStatus, ModelMlEngine
from rest.utils import get_scoped_session
from os import path
from config import fs, app
from rest.utils import zip_dir
from zipfile import ZipFile


# Train a ML Model by calling spark-submit in a shell script, where parameters of the cluster are set
# then wait for the process to finish and update the DB consequently
def run_training_algorithm(engine, model_id, timeout=None):
    # this is a separate thread, we need a scoped session to avoid race conditions
    Session = get_scoped_session(engine)
    session = Session()
    model = session.query(Model).get(model_id)

    if model.training_algorithm is None:
        training_algorithm_uri = path.join("hdfs://" + app.config["HDFS_ROOT_DIR"],
                                           app.config["HDFS_NOT_TRAINED_MODELS_DIR"],
                                           str(model_id),
                                           model.training_algorithm_file_name)
    else:
        training_algorithm_uri = path.join("hdfs://" + app.config["HDFS_ROOT_DIR"],
                                           app.config["HDFS_NOT_TRAINED_MODELS_DIR"],
                                           str(model_id),
                                           model.training_algorithm.file_name)

    dataset_uri = path.join("hdfs://" + app.config["HDFS_ROOT_DIR"],
                            app.config["HDFS_NOT_TRAINED_MODELS_DIR"],
                            str(model_id),
                            model.dataset_file_name)
    try:
        if model.ml_engine == ModelMlEngine.spark:
            trained_model_uri = path.join("hdfs://" + app.config["HDFS_ROOT_DIR"],
                                          app.config["HDFS_NOT_TRAINED_MODELS_DIR"],
                                          str(model_id),
                                          "staging/")
        elif model.ml_engine == ModelMlEngine.bigdl:
            trained_model_uri = path.join("hdfs://" + app.config["HDFS_ROOT_DIR"],
                                          app.config["HDFS_MODELS_DIR"], str(model_id))
        else:
            raise Exception("ML engine cannot be '" + str(model.ml_engine) + "'.")

        # Launch training with spark-submit
        completed_process = subprocess.run(
            args=["./rest-spark-submit.sh",
                  training_algorithm_uri,
                  dataset_uri,
                  trained_model_uri],
            text=True,
            timeout=timeout,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        print(completed_process.stdout)

        if completed_process.returncode != 0:
            print(completed_process.stdout)
            raise Exception("Spark-submit exited with a non-zero exit code.",
                            completed_process.returncode)
    except Exception as e:
        print("Model", model_id, "training failed:", str(e))
        model.status = ModelStatus.training_failed
    else:
        zip_locally_trained_model_files(model_id, model.ml_engine)
        model.status = ModelStatus.trained
        model.validity = True
        model.training_timestamp = datetime.utcnow()
    finally:
        session.commit()
        Session.remove()


def zip_locally_trained_model_files(model_id, ml_engine):
    model_folder = path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_MODELS_DIR"])

    # if Spark model, first zip the trained model folder
    if ml_engine == ModelMlEngine.spark:
        staging_folder = path.join(app.config["LOCAL_HDFS_DIR"] + app.config["HDFS_ROOT_DIR"],
                                   app.config["HDFS_NOT_TRAINED_MODELS_DIR"], str(model_id), "staging/")
        zip_fd = fs.open(path.join(model_folder, str(model_id), "model.zip"), mode='wb')
        zip_h = ZipFile(zip_fd, "w")
        zip_dir(staging_folder, zip_h)
        zip_h.close()
        zip_fd.close()

    # then zip the trained model file with the inference class
    model_id_folder = path.join(app.config["LOCAL_HDFS_DIR"] + app.config["HDFS_ROOT_DIR"],
                                app.config["HDFS_MODELS_DIR"], str(model_id))
    zip_fd = fs.open(path.join(model_folder, str(model_id) + "_trained_model.zip"), mode='wb')
    zip_h = ZipFile(zip_fd, "w")
    zip_dir(model_id_folder, zip_h)
    zip_h.close()
    zip_fd.close()
