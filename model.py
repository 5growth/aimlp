from config import db, login_manager
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.sql import case, and_
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from marshmallow import fields
from flask_login import UserMixin
from rest.utils import EnumField
from flask import url_for
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


# for semplicity, only a set of service types are available
class ServiceType(str, enum.Enum):
    automotive = "automotive"
    digital_twin = "digital twin"
    content_delivery = "content delivery"


# for semplicity, only a set of scopes are available
class Scope(str, enum.Enum):
    slice_sharing = "slice sharing"
    forecasting = "forecasting"
    scaling = "scaling"


class ModelStatus(str, enum.Enum):
    trained = "trained"
    training = "training"
    not_trained = "not trained"
    training_failed = "training failed"
    processing = "processing"


class Dataset(db.Model):
    __tablename__ = "dataset"
    dataset_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    service_type = db.Column(db.Enum(ServiceType))
    validity_expiration_timestamp = db.Column(db.DateTime)
    author = db.Column(db.String(50))
    creation_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    file_name = db.Column(db.String(100))
    external = db.Column(db.Boolean, default=False)


class TrainingAlgorithm(db.Model):
    __tablename__ = "training_algorithm"
    training_algorithm_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    scope = db.Column(db.Enum(Scope))
    ml_engine = db.Column(db.Enum(ModelMlEngine))
    author = db.Column(db.String(50))
    creation_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    external = db.Column(db.Boolean, default=False)
    file_name = db.Column(db.String(100))
    output_file_name = db.Column(db.String(100))


class InferenceClass(db.Model):
    __tablename__ = "inference_class"
    inference_class_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    file_name = db.Column(db.String(100))


class Model(db.Model):
    __tablename__ = "model"
    model_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    status = db.Column(db.Enum(ModelStatus), default=ModelStatus.not_trained)
    validity = db.Column(db.Boolean, default=False)
    external = db.Column(db.Boolean, default=False)
    validity_expiration_timestamp = db.Column(db.DateTime)
    training_timestamp = db.Column(db.DateTime)
    _author = db.Column(db.String(50))
    creation_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    accuracy = db.Column(db.Float)
    latest_update = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.dataset_id'))
    dataset = db.relationship('Dataset')
    training_algorithm_id = db.Column(db.Integer, db.ForeignKey('training_algorithm.training_algorithm_id'))
    training_algorithm = db.relationship('TrainingAlgorithm')
    trained_model_file_name = db.Column(db.String(100))
    inf_class_file_name = db.Column(db.String(100))
    training_algorithm_file_name = db.Column(db.String(100))
    dataset_file_name = db.Column(db.String(100))
    _scope = db.Column(db.Enum(Scope))
    _service_type = db.Column(db.Enum(ServiceType))
    nsd_id = db.Column(db.String(200))
    # scope = association_proxy('training_algorithm', 'scope')
    # service_type = association_proxy('dataset', 'service_type')
    _ml_engine = db.Column(db.Enum(ModelMlEngine))
    inference_class_id = db.Column(db.Integer, db.ForeignKey('inference_class.inference_class_id'))
    inference_class = db.relationship('InferenceClass')

    @hybrid_property
    def model_file_url(self):
        if self.validity and self.status == ModelStatus.trained:
            return url_for('get_model_file', model_id=self.model_id)

    @hybrid_property
    def download_file_name(self):
        return str(self.model_id) + "_trained_model.zip"

    @hybrid_property
    def scope(self):
        if self._scope: return self._scope
        else: return self.training_algorithm.scope

    @scope.setter
    def scope(self, scope_value):
        self._scope = scope_value

    @scope.expression
    def scope(cls):
        return case([(cls._scope == None, TrainingAlgorithm.scope),], else_ = cls._scope)
        # return TrainingAlgorithm.scope

    @hybrid_property
    def service_type(self):
        if self._service_type: return self._service_type
        else: return self.dataset.service_type

    @service_type.setter
    def service_type(self, service_type_value):
        self._service_type = service_type_value

    @service_type.expression
    def service_type(cls):
        return case([(cls._service_type == None, Dataset.service_type),], else_ = cls._service_type)

    @hybrid_property
    def ml_engine(self):
        if self._ml_engine: return self._ml_engine
        else: return self.training_algorithm.ml_engine

    @ml_engine.setter
    def ml_engine(self, ml_engine_value):
        self._ml_engine = ml_engine_value

    @ml_engine.expression
    def ml_engine(cls):
        return case([(cls._ml_engine == None, TrainingAlgorithm.ml_engine),], else_ = cls._ml_engine)

    @hybrid_property
    def author(self):
        if not self._author:
            if self.dataset.author == self.training_algorithm.author:
                return self.dataset.author
            elif self.dataset.author and not self.training_algorithm.author:
                return self.dataset.author
            elif self.training_algorithm.author and not self.dataset.author:
                return self.dataset.author
            else:
                return self.training_algorithm.author + " & " + self.dataset.author
        else:
            return self._author

    @author.setter
    def author(self, author_value):
        self._author = author_value

    @author.expression
    def author(cls):
        return case([
            (and_(cls._author == None, Dataset.author != None, TrainingAlgorithm.author != None, Dataset.author != TrainingAlgorithm.author), TrainingAlgorithm.author + " & " + Dataset.author),
            (and_(cls._author == None, Dataset.author == TrainingAlgorithm.author), TrainingAlgorithm.author),
            (and_(cls._author == None, Dataset.author == None, TrainingAlgorithm.author != None), TrainingAlgorithm.author),
            (and_(cls._author == None, Dataset.author != None, TrainingAlgorithm.author == None), Dataset.author),
        ], else_ = cls._author)


class DatasetSchema(SQLAlchemySchema):
    class Meta:
        model = Dataset
        ordered = True

    dataset_id = auto_field()
    name = auto_field()
    creation_timestamp = auto_field()
    service_type = auto_field()
    validity_expiration_timestamp = auto_field()
    author = auto_field()
    external = auto_field()


class TrainingAlgorithmSchema(SQLAlchemySchema):
    class Meta:
        model = TrainingAlgorithm
        ordered = True

    training_algorithm_id = auto_field()
    name = auto_field()
    scope = auto_field()
    ml_engine = auto_field()
    author = auto_field()
    creation_timestamp = auto_field()


class ModelSchema(SQLAlchemySchema):
    class Meta:
        model = Model
        # in production order should be avoided
        ordered = True

    model_id = auto_field()
    name = auto_field()
    status = auto_field()
    # service_type = EnumField(ServiceType)
    nsd_id = auto_field()
    scope = EnumField(Scope)
    ml_engine = EnumField(ModelMlEngine)
    latest_update = auto_field()
    creation_timestamp = auto_field()
    training_timestamp = auto_field()
    validity_expiration_timestamp = auto_field()
    validity = auto_field()
    external = auto_field()
    author = fields.String()
    accuracy = auto_field()
    # dataset = fields.Nested(DatasetSchema)
    # training_algorithm = fields.Nested(TrainingAlgorithmSchema)
    model_file_url = fields.URL()