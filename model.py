from config import db, ma, login_manager
from datetime import datetime
# from sqlalchemy.ext.hybrid import hybrid_property
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field, fields
from flask_login import UserMixin
import enum


# define user_loader callback to reload user object from the user ID stored in the session
@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    surname = db.Column(db.String(1000))
    affiliation = db.Column(db.String(1000))

class ModelMlEngine(str, enum.Enum):
    spark = "spark"
    bigdl = "bigdl"

class ServiceType(str, enum.Enum):
    automotive = "automotive"
    digitalTwin = "digital_twin"
    contentDelivery = "content_delivery"

class ModelStatus(str, enum.Enum):
    trained = "trained"
    training = "training"
    not_trained = "not trained"
    training_failed = "training failed"

class Dataset(db.Model):
    __tablename__ = "dataset"
    dataset_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    scope = db.Column(db.String(50))
    type = db.Column(db.Enum(ModelMlEngine))
    service_type = db.Column(db.Enum(ServiceType))
    validity_expiration_timestamp = db.Column(db.DateTime)
    author = db.Column(db.String(50))
    creation_timestamp = db.Column(db.DateTime, default=datetime.utcnow())
    file_name = db.Column(db.String(100))
    external = db.Column(db.Boolean, default=False)

class Model(db.Model):
    __tablename__ = "model"
    model_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    scope = db.Column(db.String(50))
    type = db.Column(db.Enum(ModelMlEngine))
    status = db.Column(db.Enum(ModelStatus), default=ModelStatus.not_trained)
    validity = db.Column(db.Boolean, default=False)
    external = db.Column(db.Boolean, default=False)
    validity_expiration_timestamp = db.Column(db.DateTime)
    training_timestamp = db.Column(db.DateTime)
    author = db.Column(db.String(50))
    creation_timestamp = db.Column(db.DateTime, default=datetime.utcnow())
    accuracy = db.Column(db.Float)
    latest_update = db.Column(db.DateTime, default=datetime.utcnow)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.dataset_id'))
    dataset = db.relationship('Dataset')
    file_name = db.Column(db.String(100))

    # commented till the information model for the model file path is figured out
    # @hybrid_property
    # def url(self):
    #     return("/model/" + str(self.model_id) + "/url")


class DatasetSchema(SQLAlchemySchema):
    class Meta:
        model = Dataset
        ordered = True

    dataset_id = auto_field()
    name = auto_field()
    creation_timestamp = auto_field()


class ModelSchema(SQLAlchemySchema):
    class Meta:
        model = Model
        # in production order should be avoided
        ordered = True

    model_id = auto_field()
    name = auto_field()
    type = auto_field()
    status = auto_field()
    validity = auto_field()
    external = auto_field()
    training_timestamp = auto_field()
    author = auto_field()
    creation_timestamp = auto_field()
    accuracy = auto_field()
    latest_update = auto_field()
    dataset = fields.Nested(DatasetSchema)
    # first figure out the information model for the relation with the model file path
    # url = fields.Url(dump_only=True)
