import subprocess
from datetime import datetime
from model import Model, ModelStatus
from rest.utils import get_scoped_session


# Train a ML Model by calling spark-submit in a shell script, where parameters of the cluster are set
# then wait for the process to finish and update the DB consequently
def train_model(engine, model_id, timeout=None):
    # this is a separate thread, we need a scoped session to avoid race conditions
    Session = get_scoped_session(engine)
    session = Session()
    model = session.query(Model).get(model_id)

    # Launch training with spark-submit
    try:
        completed_process = subprocess.run(
            ["./rest-spark-submit.sh", "/home/worker/"+model.training_algorithm_file_name],
            text=True,
            timeout=timeout,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

        if completed_process.returncode != 0:
            print(completed_process.stdout)
            raise Exception("Spark-submit exited with a non-zero exit code",
                            completed_process.returncode)
    except Exception as e:
        print("Model", model_id,"training failed:", str(e))
        model.status = ModelStatus.training_failed
    else:
        model.status = ModelStatus.trained
        model.training_timestamp = datetime.utcnow()
    finally:
        model.latest_update = datetime.utcnow()
        session.commit()
        Session.remove()
