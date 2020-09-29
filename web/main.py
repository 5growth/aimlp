from flask import Blueprint, render_template, Flask, request, redirect, url_for, abort, current_app, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from config import db
from model import Model

main = Blueprint('main', __name__)
valid_extension = ['.h5']
upload_path = 'uploaded_models'

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/upload')
@login_required
def upload():
    return render_template('upload.html', name=current_user.name)

@main.route('/upload', methods=['POST'])
@login_required
def upload_post():
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
    modelValidity = datetime.strptime(modelValidity,"%Y-%m-%d %H:%M")
    modelTraining = datetime.strptime(modelTraining,"%Y-%m-%d %H:%M")
    modelCreation = datetime.strptime(modelCreation,"%Y-%m-%d %H:%M")

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
    if (modelAccuracy.find(",")!=-1):
        print(modelAccuracy)
        print("Entered")
        modelAccuracy=modelAccuracy.replace(',','.')
        print(modelAccuracy)
    try:
        float(modelAccuracy)
    except ValueError:
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
        return redirect(url_for('main.upload'))
    else:
        uploadedFile.save(os.path.join(upload_path, modelFilename))

        new_model = Model(name=modelName, scope=modelScope, type=modelType, external=True, accuracy=modelAccuracy,
            status="trained", validity_expiration_timestamp=modelValidity, training_timestamp=modelTraining, 
            author=authorAffiliation, creation_timestamp=modelCreation, latest_update=modelCreation, file_name=modelFilename)
        db.session.add(new_model)
        db.session.commit()

        return render_template('upload.html', 
            show_report=1, name=current_user.name, surname=current_user.surname, modelAccuracy=modelAccuracy,
            modelName=modelName, modelScope=modelScope, modelType=modelType,
            modelCreation=modelCreation, modelValidity=modelValidity, modelTraining=modelTraining,
            authorAffiliation=authorAffiliation, modelFilename=modelFilename)
