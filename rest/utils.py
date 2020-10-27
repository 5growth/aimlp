from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from marshmallow.validate import OneOf
from marshmallow import fields


# Define fs as an object with method "exists", which returns false,
# in order to correctly handle the fs.exists call when HDFS isn't available
def dummy_fs():
    return type("fsHandler", (object,), {"exists": lambda self: False})

def get_scoped_session(engine):
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)

def reset_db(forced=False):
    from model import Model, Dataset, ServiceType, Scope, TrainingAlgorithm, ModelMlEngine
    from config import db, app

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

    random_forest_algo = TrainingAlgorithm(name="automotive_scaling_random_forest_spark", scope=Scope.scaling,
                                           file_name="rest-spark-scaling-training.py", ml_engine=ModelMlEngine.spark,
                                           author="Polito")
    neural_network_algo = TrainingAlgorithm(name="automotive_scaling_nn_bigdl", scope=Scope.scaling,
                                            file_name="rest-bigdl-scaling-training.py", ml_engine=ModelMlEngine.bigdl,
                                            author="Polito")
    scaling_dataset = Dataset(name="evs_scaling", service_type=ServiceType.automotive, scope=Scope.forecasting,
                              author="Polito")
    random_forest = Model(name="random forest for scaling",
                          trained_model_file_name="dataset.csv",
                          external=False,
                          dataset=scaling_dataset,
                          training_algorithm=random_forest_algo)
    neural_network = Model(name="neural network for scaling",
                           trained_model_file_name="model.bigdl",
                           external=False,
                           dataset=scaling_dataset,
                           training_algorithm=neural_network_algo)
    db.session.add_all([random_forest, neural_network])
    db.session.commit()

def EnumField(enum_class):
    return fields.Field(validate=[OneOf(choices=[e.value for e in enum_class])])