from model import *
from flask import Response, send_file, request, abort
from config import app
from rest import controller
from rest.utils import reset_db
from sqlalchemy.exc import InvalidRequestError
from marshmallow import ValidationError
from rest.kafka_connector_manager import print_streaming_status

@app.route('/models', methods=['GET'])
def get_models():
    if not request.args:
        models = Model.query.all()
    else:
        try:
            models = Model.query.filter_by(**request.args).all()
        except InvalidRequestError as e:
            app.logger.error(e)
            # Bad request if the request fails, i.e. the filtered property has not been found
            abort(400)
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

@app.route("/dataset_collectors/process/<nsd_id>", methods=["GET"])
def process_dataset(nsd_id):
    controller.process_data_collectors(nsd_id)
    return ('', 202)

@app.route("/dataset_collectors/get/<nsd_id>", methods=["GET"])
def get_collected_dataset(nsd_id):
    dataset = controller.get_dataset_file(nsd_id)
    return send_file(dataset)

@app.route('/dataset_collectors', methods=['GET'])
def get_data_collectors():
    #print_streaming_status()
    collectors = DatasetCollector.query.all()
    return Response(CollectorSchema(many=True).dumps(collectors), mimetype="text/json")

@app.route('/dataset_collectors/<kafka_topic>', methods=['PUT', 'DELETE', 'GET'])
def manage_data_collector(kafka_topic):
    if request.method == "PUT":
        try:
            collector = CollectorSchema().load(request.json)
        except ValidationError as err:
            app.logger.warning(err.messages)
            abort(400)

        # check if the kakfa topics from path and body are the same
        if kafka_topic != collector["kafka_topic"]:
            abort(400)

        # check if the collector is already active, do not instantiate it again
        active_collector = DatasetCollector.query.filter_by(kafka_topic=kafka_topic).first()
        if active_collector is None:
            active_collector = controller.put_data_collector(collector)

    elif request.method == "DELETE":
        active_collector = DatasetCollector.query.filter_by(kafka_topic=kafka_topic).first()
        if active_collector is None:
            abort(404)
        else:
            active_collector = controller.delete_data_collector(active_collector)

    elif request.method == "GET":
        active_collector = DatasetCollector.query.filter_by(kafka_topic=kafka_topic).first()
        if active_collector is None:
            abort(404)

    else:
        abort(500)

    return Response(CollectorSchema().dumps(active_collector), mimetype="text/json")


@app.route('/reset')
def reset_status():
    if "forced" in request.args:
        reset_db(request.args["forced"])
    else:
        reset_db()
    return Response()
