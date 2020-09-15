from flask import Blueprint, render_template, Flask, request, redirect, url_for, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

main = Blueprint('main', __name__)
valid_extension = ['.h5', '.zip']
upload_path = 'uploads'

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/upload')
@login_required
def upload():
    return render_template('upload.html',data='No file uploaded yet', name=current_user.name)

@main.route('/upload', methods=['POST'])
@login_required
def upload_post():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)

    # If the filename is not empty, then check if the extension is supported and eventually save the file
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in valid_extension:
            abort(400)

        print(upload_path)

        uploaded_file.save(os.path.join(upload_path, filename))
        return render_template('upload.html',data=filename+ " has been correctly uploaded!", name=current_user.name)


@main.errorhandler(400)
def wrongFile(e):
    return render_template('upload.html', name=current_user.name, data='The file you are trying to upload is not supported!')