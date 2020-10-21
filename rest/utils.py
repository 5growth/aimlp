from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

# Define fs as an object with method "exists", which returns false,
# in order to correctly handle the fs.exists call when HDFS isn't available
def dummy_fs():
    return type("fsHandler", (object,), {"exists": lambda self: False})

def get_scoped_session(engine):
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)

def reset_db():
    from model import Model, Dataset, ServiceType, Scope
    from config import db, app

    app.logger.warning("The Model and Dataset tables have been reset to default")
    Model.__table__.drop(db.engine)
    Dataset.__table__.drop(db.engine)
    Model.__table__.create(db.engine)
    Dataset.__table__.create(db.engine)

    scaling_dataset = Dataset(name="evs_scaling", service_type=ServiceType.automotive, scope=Scope.forecasting)
    random_forest = Model(name="random forest for scaling",
                          validity=True,
                          author="Polito",
                          file_name="dataset.csv",
                          external=False,
                          dataset=scaling_dataset,
                          scope="scaling",
                          training_algorithm_file_name="rest-spark-scaling-training.py")
    neural_network = Model(name="neural network for scaling",
                           validity=True,
                           author="Polito",
                           file_name="model.bigdl",
                           external=False,
                           dataset=scaling_dataset,
                           scope="scaling",
                           training_algorithm_file_name="rest-bigdl-scaling-training.py")
    db.session.add_all([random_forest, neural_network])
    db.session.commit()
