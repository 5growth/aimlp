from model import *
from flask import Response, send_file, request
from config import app
from rest import controller
from rest.utils import reset_db

@app.route('/models', methods=['GET'])
def get_models():
    models = Model.query.filter_by(**request.args)
    return Response(ModelSchema(many=True).dumps(models), mimetype='text/json')


@app.route('/models/filterByScope/<scope>')
def get_model_by_scope(scope):
    models = Model.query.filter_by(scope=scope).all()
    return Response(ModelSchema(many=True).dumps(models), mimetype='text/json')


@app.route('/models/<model_id>', methods=['GET'])
def get_model_id(model_id):
    model = Model.query.get_or_404(model_id)
    return Response(ModelSchema().dumps(model), mimetype='text/json')


@app.route('/models/<model_id>/train', methods=['GET'])
def train_model(model_id):
    model = controller.start_training(model_id)
    return Response(ModelSchema().dumps(model), mimetype='text/json')


@app.route('/models/<model_id>/file', methods=['GET'])
def get_model_file(model_id):
    (model_file, file_name) = controller.get_model_file(model_id)
    return send_file(model_file, as_attachment=True, attachment_filename=file_name)


@app.route('/reset')
def reset_status():
    reset_db()
    return Response()
