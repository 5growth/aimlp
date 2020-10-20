from flask import Blueprint, render_template, Flask, request, redirect, url_for, abort, current_app, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from config import db
from model import Model, Dataset

main = Blueprint('main', __name__)
valid_extension = ['.jar','.h5']
valid_extensionTBT = ['.jar','.h5']
valid_extensionDataset = ['.jar','.zip']

upload_path = 'uploaded_models'
upload_pathTBT = 'uploaded_modelsTBT'
upload_pathDataset = 'uploaded_datasets'

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/uploadModel')
@login_required
def uploadModel():
    return render_template('uploadModel.html', name=current_user.name)

@main.route('/uploadModel', methods=['POST'])
@login_required
def uploadModel_post():
    modelName = str(request.form.get("name"))
    modelScope = str(request.form.get("scope"))
    modelType = str(request.form.get("type"))
    modelCreation = str(datetime.now().strftime("%Y-%m-%d %H:%M"))
    modelValidity = str(request.form.get("validity")).replace("T", " ")
    modelTraining = str(request.form.get("training")).replace("T", " ")
    uploadedFile = request.files['file']
    authorAffiliation = current_user.affiliation
    modelFilename = secure_filename(uploadedFile.filename)
    modelAccuracy = str(request.form.get("accuracy"))

    #convert times
    try:
        modelValidity = datetime.strptime(modelValidity,"%Y-%m-%d %H:%M")
    except ValueError:
        modelValidity = ""
    try:
        modelTraining = datetime.strptime(modelTraining,"%Y-%m-%d %H:%M")
    except ValueError:
        modelTraining = ""    
    try:
        modelCreation = datetime.strptime(modelCreation,"%Y-%m-%d %H:%M")
    except ValueError:
        modelCreation = ""

    toBeChecked = "<br/>"
    if (modelName == "None" or modelName == ""):
        toBeChecked = toBeChecked+"* Name is wrong [cannot be empty]<br/>"
    if (modelScope == "None" or modelScope == ""):
        toBeChecked = toBeChecked+"* Scope is wrong [cannot be empty]<br/>"
    if (modelType == "None" or modelType == ""):
        toBeChecked = toBeChecked+"* Type is wrong [cannot be empty]<br/>"
    if (modelValidity == "None" or modelValidity == ""):
        toBeChecked = toBeChecked+"* Validity Expiration is wrong [cannot be empty]<br/>"
    if (modelTraining == "None" or modelTraining == ""):
        toBeChecked = toBeChecked+"* Training Time is wrong [cannot be empty]<br/>"
    if (modelAccuracy == "" ):
    	modelAccuracy = None
    elif (modelAccuracy.find(",")!=-1):
        print(modelAccuracy)
        print("Entered")
        modelAccuracy=modelAccuracy.replace(',','.')
        print(modelAccuracy)
    try:
        float(modelAccuracy)
    except (ValueError, TypeError):
        modelAccuracy = None

    if modelFilename != '':
        file_ext = os.path.splitext(modelFilename)[1]
        if file_ext not in valid_extension:
            toBeChecked = toBeChecked+"* Model file extension: " + file_ext + " is not a correct extension!"
    else:
        toBeChecked = toBeChecked+"* You must include your model file!"

    #print(modelName,modelScope,modelType,modelCreation,modelValidity,modelTraining,modelAuthor,modelFilename)

    if (toBeChecked != "<br/>"):
        flash('Please check the following issues: ' + toBeChecked)
        return redirect(url_for('main.uploadModel'))
    else:
        uploadedFile.save(os.path.join(upload_path, modelFilename))

        new_model = Model(name=modelName, scope=modelScope, type=modelType, external=True, accuracy=modelAccuracy,
            status="trained", validity_expiration_timestamp=modelValidity, training_timestamp=modelTraining, 
            author=authorAffiliation, creation_timestamp=modelCreation, latest_update=modelCreation, file_name=modelFilename)
        db.session.add(new_model)
        db.session.commit()

        return render_template('uploadModel.html', 
            show_report=1, name=current_user.name, surname=current_user.surname, modelAccuracy=modelAccuracy,
            modelName=modelName, modelScope=modelScope, modelType=modelType,
            modelCreation=modelCreation, modelValidity=modelValidity, modelTraining=modelTraining,
            authorAffiliation=authorAffiliation, modelFilename=modelFilename)

@main.route('/uploadDataset')
@login_required
def uploadDataset():
    return render_template('uploadDataset.html', name=current_user.name)

@main.route('/uploadDataset', methods=['POST'])
@login_required
def uploadDataset_post():
    datasetName = str(request.form.get("name"))
    datasetScope = str(request.form.get("scope"))
    datasetType = str(request.form.get("type"))
    serviceType = str(request.form.get("serviceType"))
    datasetValidity = str(request.form.get("validity")).replace("T", " ")
    uploadedFile = request.files['file']
    authorAffiliation = current_user.affiliation
    datasetFilename = secure_filename(uploadedFile.filename)
    
    #convert times
    try:
        datasetValidity = datetime.strptime(datasetValidity,"%Y-%m-%d %H:%M")
    except ValueError:
        datasetValidity = None

    toBeChecked = "<br/>"
    if (datasetName == "None" or datasetName == ""):
        toBeChecked = toBeChecked+"* Name is wrong [cannot be empty]<br/>"
    if (datasetScope == "None" or datasetScope == ""):
        toBeChecked = toBeChecked+"* Scope is wrong [cannot be empty]<br/>"
    if (datasetType == "None" or datasetType == ""):
        toBeChecked = toBeChecked+"* Type is wrong [cannot be empty]<br/>"
    if (serviceType == "None" or serviceType == ""):
        toBeChecked = toBeChecked+"* Service type is wrong [cannot be empty]<br/>"
    
    if datasetFilename != '':
        file_ext = os.path.splitext(datasetFilename)[1]
        if file_ext not in valid_extensionDataset:
            toBeChecked = toBeChecked+"* Dataset file extension: " + file_ext + " is not a correct extension!"
    else:
        toBeChecked = toBeChecked+"* You must include your dataset file!"

    #print(modelName,modelScope,modelType,modelCreation,modelValidity,modelTraining,modelAuthor,modelFilename)

    if (toBeChecked != "<br/>"):
        flash('Please check the following issues: ' + toBeChecked)
        return redirect(url_for('main.uploadDataset'))
    else:
        uploadedFile.save(os.path.join(upload_pathDataset, datasetFilename))

        new_dataset = Dataset(name=datasetName, scope=datasetScope, type=datasetType, external=True,
             validity_expiration_timestamp=datasetValidity, author=authorAffiliation, service_type=serviceType, file_name=datasetFilename)
        db.session.add(new_dataset)
        db.session.commit()

        return render_template('uploadDataset.html', 
            show_report=1, name=current_user.name, surname=current_user.surname, datasetName=datasetName, 
            datasetScope=datasetScope, datasetType=datasetType, serviceType=serviceType,
            datasetValidity=datasetValidity,authorAffiliation=authorAffiliation, datasetFilename=datasetFilename)

@main.route('/uploadModelTBT')
@login_required
def uploadModelTBT():
    return render_template('uploadModelTBT.html', name=current_user.name)

@main.route('/uploadModelTBT', methods=['POST'])
@login_required
def uploadModelTBT_post():
    modelName = str(request.form.get("name"))
    modelScope = str(request.form.get("scope"))
    modelType = str(request.form.get("type"))
    serviceType = str(request.form.get("serviceType"))

    uploadedFile = request.files['file']
    authorAffiliation = current_user.affiliation
    modelFilename = secure_filename(uploadedFile.filename)

    toBeChecked = "<br/>"
    if (modelName == "None" or modelName == ""):
        toBeChecked = toBeChecked+"* Name is wrong [cannot be empty]<br/>"
    if (modelScope == "None" or modelScope == ""):
        toBeChecked = toBeChecked+"* Scope is wrong [cannot be empty]<br/>"
    if (modelType == "None" or modelType == ""):
        toBeChecked = toBeChecked+"* Type is wrong [cannot be empty]<br/>"
    if (serviceType == "None" or serviceType == ""):
        toBeChecked = toBeChecked+"* Service type is wrong [cannot be empty]<br/>"

    if modelFilename != '':
        file_ext = os.path.splitext(modelFilename)[1]
        if file_ext not in valid_extensionTBT:
            toBeChecked = toBeChecked+"* Model file extension: " + file_ext + " is not a correct extension!"
    else:
        toBeChecked = toBeChecked+"* You must include your model file!"

    #print(modelName,modelScope,modelType,modelCreation,modelValidity,modelTraining,modelAuthor,modelFilename)

    if (toBeChecked != "<br/>"):
        flash('Please check the following issues: ' + toBeChecked)
        return redirect(url_for('main.uploadModelTBT'))
    else:
        uploadedFile.save(os.path.join(upload_pathTBT, modelFilename))

        #new_model = Model(name=modelName, scope=modelScope, type=modelType, external=True, accuracy=modelAccuracy,
        #    status="trained", validity_expiration_timestamp=modelValidity, training_timestamp=modelTraining, 
        #    author=authorAffiliation, creation_timestamp=modelCreation, latest_update=modelCreation, file_name=modelFilename)
        #db.session.add(new_model)
        #db.session.commit()

        return render_template('uploadModelTBT.html', 
            show_report=1, name=current_user.name, surname=current_user.surname, modelName=modelName, 
            modelScope=modelScope, modelType=modelType, serviceType=serviceType,
            authorAffiliation=authorAffiliation, modelFilename=modelFilename)
