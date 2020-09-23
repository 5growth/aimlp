from config import db, app
from model import *

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    scaling_dataset = Dataset(name="evs_scaling")
    random_forest = Model(name="random forest for scaling",
                          validity=True,
                          author="Polito",
                          file_name="giulia.jpg",
                          trainable=True,
                          dataset=scaling_dataset,
                          scope="scaling")
    db.session.add(random_forest)
    db.session.add(Model(model_id=4, name="test"))
    db.session.add(Model())
    db.session.commit()
    # app.run(debug=True)
