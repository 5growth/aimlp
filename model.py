from config import db, ma
from datetime import datetime
# from sqlalchemy.ext.hybrid import hybrid_property
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
import enum


class ModelMlEngine(str, enum.Enum):
    spark = "spark"
    bigdl = "bigdl"

class ModelStatus(str, enum.Enum):
    trained = "trained"
    training = "training"
    not_trained = "not trained"
    training_failed = "training failed"

class Model(db.Model):
    __tablename__ = "model"
    model_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    type = db.Column(db.Enum(ModelMlEngine))
    status = db.Column(db.Enum(ModelStatus), default=(ModelStatus.not_trained))
    validity = db.Column(db.Boolean, default=False)
    training_time = db.Column(db.DateTime)
    creator = db.Column(db.String(50))
    creation_time = db.Column(db.DateTime, default=datetime.utcnow)
    accuracy = db.Column(db.Float)
    latest_update = db.Column(db.DateTime, default=datetime.utcnow)
    file_name = db.Column(db.String(50))

    # commented till the information model for the model file path is figured out
    # @hybrid_property
    # def url(self):
    #     return("/model/" + str(self.model_id) + "/url")


class ModelSchema(SQLAlchemySchema):
    class Meta:
        model = Model
        # in production order should be avoided
        ordered = True

    model_id = auto_field()
    name = auto_field()
    type =  auto_field()
    status = auto_field()
    validity = auto_field()
    training_time = auto_field()
    creator = auto_field()
    creation_time = auto_field()
    accuracy = auto_field()
    latest_update = auto_field()
    # first figure out the information model for the relation with the model file path
    # url = fields.Url(dump_only=True)
