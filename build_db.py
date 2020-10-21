from config import db
from model import Model, Dataset, Scope, ServiceType

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    scaling_dataset = Dataset(name="evs_scaling", service_type=ServiceType.automotive)
    random_forest = Model(name="random forest for scaling",
                            validity=True,
                            author="Polito",
                            file_name="dataset.csv",
                            external=False,
                            dataset=scaling_dataset,
                            scope=Scope.scaling,
                            training_algorithm_file_name="rest-spark-scaling-training.py")
    neural_network = Model(name="neural network for scaling",
                            validity = True,
                            author = "Polito",
                            file_name = "model.bigdl",
                            external = False,
                            dataset = scaling_dataset,
                            scope = Scope.scaling,
                            training_algorithm_file_name = "rest-bigdl-scaling-training.py")
    db.session.add(random_forest)
    db.session.add(Model(model_id=4, name="test"))
    db.session.add(neural_network)
    db.session.commit()
    # app.run(debug=True)
