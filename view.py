from model import *
from flask import Response
from config import app

@app.route('/')
def home():
    return "Upload a model"

@app.route('/models/', methods=['GET'])
def get_models():
    models = []
    for m in Model.query.all():
        models.append(m)
    return Response(ModelSchema(many=True).dumps(models), mimetype='text/json')

@app.route('/models/<id>', methods=['GET'])
def get_model_id(id):
    model = Model.query.get_or_404(id)
    return Response(ModelSchema().dumps(model), mimetype='text/json')