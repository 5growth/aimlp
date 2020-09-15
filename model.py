from config import db, ma, login_manager
from datetime import datetime
# from sqlalchemy.ext.hybrid import hybrid_property
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from flask_login import UserMixin
import enum


# define user_loader callback to reload user object from the user ID stored in the session
@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))


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
