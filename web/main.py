from flask import Blueprint, render_template, Flask, request, redirect, url_for, abort, current_app, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import threading
from datetime import datetime
import datetime as dt
from config import db, fs, app
from model import Model, Dataset, Scope, ModelMlEngine, ModelStatus
from rest.utils import zip_externally_trained_model_files

main = Blueprint('main', __name__)
valid_extension_model = ['.zip', '.h5']
valid_extension_inf_class = ['.py', '.jar']
valid_extension_training_algorithm = ['.py', '.jar']

upload_path = 'uploaded_models'


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/uploadModel')
@login_required
def uploadModel():
    return render_template('uploadModel.html', name=current_user.name, scopes=Scope)


@main.route('/uploadModel', methods=['POST'])
@login_required
def uploadModel_post():
    modelName = str(request.form.get("name"))
    modelScope = str(request.form.get("scope"))
    modelNSD = str(request.form.get("nsd_id"))
    modelValidity = str(request.form.get("validity")).replace("T", " ")
    modelTraining = str(request.form.get("training")).replace("T", " ")
    uploadedModel = request.files['model']
    uploadedInfClass = request.files['inf_class']
    authorAffiliation = current_user.affiliation
    modelFilename = secure_filename(uploadedModel.filename)
    infClassFilename = secure_filename(uploadedInfClass.filename)
    modelAccuracy = str(request.form.get("accuracy"))

    # convert times
    try:
        modelValidity = datetime.strptime(modelValidity, "%Y-%m-%d %H:%M")
        if(modelValidity.date()>dt.datetime.today().date()):
            print("Expires in the future")
        if(modelValidity.date()<dt.datetime.today().date()):
            print("Expires in the past")
        if (modelValidity.date() == dt.datetime.today().date()):
            print("Expires today")
    except ValueError:
        modelValidity = ""
    try:
        modelTraining = datetime.strptime(modelTraining, "%Y-%m-%d %H:%M")
    except ValueError:
        modelTraining = ""

    toBeChecked = "<br/>"
    if (modelName == "None" or modelName == ""):
        toBeChecked = toBeChecked + "* Name is wrong [cannot be empty]<br/>"
    if (modelScope == "None" or modelScope == ""):
        toBeChecked = toBeChecked + "* Scope is wrong [cannot be empty]<br/>"
    if (modelNSD == "None" or modelNSD == ""):
        toBeChecked = toBeChecked + "* Network Service Descriptor is wrong [cannot be empty]<br/>"
    if (modelValidity == "None" or modelValidity == ""):
        toBeChecked = toBeChecked + "* Validity Expiration is wrong [cannot be empty]<br/>"
    if (modelTraining == "None" or modelTraining == ""):
        toBeChecked = toBeChecked + "* Training Time is wrong [cannot be empty]<br/>"
    if (modelAccuracy == ""):
        modelAccuracy = None
    elif (modelAccuracy.find(",") != -1):
        print(modelAccuracy)
        print("Entered")
        modelAccuracy = modelAccuracy.replace(',', '.')
        print(modelAccuracy)
    try:
        float(modelAccuracy)
    except (ValueError, TypeError):
        modelAccuracy = None

    if modelFilename != '':
        file_ext = os.path.splitext(modelFilename)[1]
        if file_ext not in valid_extension_model:
            toBeChecked = toBeChecked + "* Model file extension: " + file_ext + " is not a correct extension!<br/>"
    else:
        toBeChecked = toBeChecked + "* You must include your model file!<br/>"

    if infClassFilename != '':
        file_ext = os.path.splitext(infClassFilename)[1]
        if file_ext not in valid_extension_inf_class:
            toBeChecked = toBeChecked + "* Inference class file extension: " + file_ext + " is not a correct extension!"
    else:
        toBeChecked = toBeChecked + "* You must include your inference class python file!"

    # print(modelName,modelScope,modelType,modelCreation,modelValidity,modelTraining,modelAuthor,modelFilename)

    if (toBeChecked != "<br/>"):
        flash('Please check the following issues: ' + toBeChecked)
        return redirect(url_for('main.uploadModel'))
    else:
        if(modelValidity.date()<dt.datetime.today().date()):
            validityInfo = ""
            validityWarning = "Warning: model expired in the past!"
        else:
            validityWarning = ""
            validityInfo = "Model expires in " + str((modelValidity.date() - dt.datetime.today().date()).days) + " day(s)"

        if(modelTraining.date()>dt.datetime.today().date()):
            trainingWarning = "Warning: model trained in the future!"
            trainingInfo = ""
        else:
            trainingInfo = "Modal was trained " + str((dt.datetime.today().date()-modelTraining.date()).days) + " day(s) ago"
            trainingWarning=""

        new_model = Model(name=modelName, scope=modelScope, nsd_id=modelNSD, external=True, accuracy=modelAccuracy,
                          status=ModelStatus.processing, validity_expiration_timestamp=modelValidity,
                          training_timestamp=modelTraining,
                          author=authorAffiliation, trained_model_file_name=modelFilename,
                          inf_class_file_name=infClassFilename)
        db.session.add(new_model)
        db.session.commit()

        # After the model correctness is checked against DB constraints, add the file in the HDFS
        fs.mkdir(os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_MODELS_DIR"], str(new_model.model_id)))
        modelFile_path = os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_MODELS_DIR"],
                                      str(new_model.model_id),
                                      modelFilename)
        infClassFile_path = os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_MODELS_DIR"],
                                         str(new_model.model_id),
                                         infClassFilename)

        fd_model = fs.open(modelFile_path, mode='wb')
        fd_inf = fs.open(infClassFile_path, mode='wb')

        uploadedModel.save(fd_model)
        uploadedInfClass.save(fd_inf)
        fd_model.close()
        fd_inf.close()

        # zip the uploaded files
        engine = db.get_engine()
        zip_files_thread = threading.Thread(target=zip_externally_trained_model_files,
                                            args=(engine, new_model.model_id))
        zip_files_thread.start()

        return render_template('uploadModel.html',
                               show_report=1, name=current_user.name, surname=current_user.surname,
                               modelAccuracy=modelAccuracy,
                               modelName=modelName, modelScope=modelScope, modelNSD_id=modelNSD,
                               modelValidity=modelValidity, modelTraining=modelTraining,
                               authorAffiliation=authorAffiliation, modelFilename=modelFilename,
                               infClassFilename=infClassFilename, validityWarning=validityWarning,
                               validityInfo=validityInfo, trainingWarning=trainingWarning, trainingInfo=trainingInfo)


@main.route('/uploadTrainingAlgorithm')
@login_required
def uploadTrainingAlgorithm():
    return render_template('uploadTrainingAlgorithm.html', name=current_user.name, scopes=Scope, engines=ModelMlEngine)

@main.route('/uploadTrainingAlgorithm', methods=['POST'])
@login_required
def uploadTrainingAlgorithm_post():
    modelName = str(request.form.get("name"))
    modelScope = str(request.form.get("scope"))
    modelNSD = str(request.form.get("nsd_id"))
    modelMlEngine = str(request.form.get("ml_engine"))
    uploadedTrainingAlgorithm = request.files['training_algorithm']
    uploadedInfClass = request.files['inf_class']
    uploadedDataset = request.files['dataset']
    authorAffiliation = current_user.affiliation
    trainingAlgorithmFilename = secure_filename(uploadedTrainingAlgorithm.filename)
    infClassFilename = secure_filename(uploadedInfClass.filename)
    datasetFilename = secure_filename(uploadedDataset.filename)

    toBeChecked = "<br/>"
    if (modelName == "None" or modelName == ""):
        toBeChecked = toBeChecked + "* Name is wrong [cannot be empty]<br/>"
    if (modelScope == "None" or modelScope == ""):
        toBeChecked = toBeChecked + "* Scope is wrong [cannot be empty]<br/>"
    if (modelNSD == "None" or modelNSD == ""):
        toBeChecked = toBeChecked + "* Network Service Descriptor is wrong [cannot be empty]<br/>"
    if (modelMlEngine == "None" or modelMlEngine == ""):
        toBeChecked = toBeChecked + "* ML Engine is wrong [cannot be empty]<br/>"

    if trainingAlgorithmFilename != '':
        file_ext = os.path.splitext(trainingAlgorithmFilename)[1]
        if file_ext not in valid_extension_training_algorithm:
            toBeChecked = toBeChecked + "* Training algorithm file extension: " + file_ext + " is not a correct extension!<br/>"
    else:
        toBeChecked = toBeChecked + "* You must include your model file!<br/>"

    if infClassFilename != '':
        file_ext = os.path.splitext(infClassFilename)[1]
        if file_ext not in valid_extension_inf_class:
            toBeChecked = toBeChecked + "* Inference Class file extension: " + file_ext + " is not a correct extension!<br/>"
    else:
        toBeChecked = toBeChecked + "* You must include your inference class file!<br/>"

    if datasetFilename == '':
        toBeChecked = toBeChecked + "* You must include your dataset file!<br/>"

    # print(modelName,modelScope,modelType,modelCreation,modelValidity,modelTraining,modelAuthor,modelFilename)

    if (toBeChecked != "<br/>"):
        flash('Please check the following issues: ' + toBeChecked)
        return redirect(url_for('main.uploadTrainingAlgorithm'))
    else:
        new_model = Model(name=modelName, scope=modelScope, nsd_id=modelNSD, external=True, ml_engine=modelMlEngine,
                          status="not_trained", author=authorAffiliation, training_algorithm_file_name=trainingAlgorithmFilename,
                          dataset_file_name=datasetFilename, inf_class_file_name=infClassFilename)
        db.session.add(new_model)
        db.session.commit()

        # After the model correctness is checked against DB constraints, add the file in the HDFS
        fs.mkdir(os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_NOT_TRAINED_MODELS_DIR"], str(new_model.model_id)))
        trainingAlgorithmFile_path = os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_NOT_TRAINED_MODELS_DIR"],str(new_model.model_id), trainingAlgorithmFilename)
        infClassFile_path = os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_MODELS_DIR"],str(new_model.model_id),infClassFilename)
        datasetFile_path = os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_NOT_TRAINED_MODELS_DIR"],str(new_model.model_id),datasetFilename)
        fs.mkdir(os.path.join(app.config["HDFS_ROOT_DIR"], app.config["HDFS_NOT_TRAINED_MODELS_DIR"],
                              str(new_model.model_id), "staging"))
        fd_training_algorithm = fs.open(trainingAlgorithmFile_path, mode='wb')
        fd_inf = fs.open(infClassFile_path, mode='wb')
        fd_dataset = fs.open(datasetFile_path, mode='wb')

        uploadedTrainingAlgorithm.save(fd_training_algorithm)
        uploadedInfClass.save(fd_inf)
        uploadedDataset.save(fd_dataset)
        fd_training_algorithm.close()
        fd_inf.close()
        fd_dataset.close()

        return render_template('uploadTrainingAlgorithm.html',
                               show_report=1, name=current_user.name, surname=current_user.surname,
                               modelName=modelName, modelScope=modelScope, modelNSD_id=modelNSD,
                               modelEngine=modelMlEngine,authorAffiliation=authorAffiliation,datasetFilename=datasetFilename,
                               trainingAlgorithmFilename=trainingAlgorithmFilename,infClassFilename=infClassFilename)