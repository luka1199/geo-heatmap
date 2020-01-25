import os
from flask import Flask, flash, request, redirect, url_for, send_from_directory, current_app
from werkzeug.utils import secure_filename
from geo_heatmap import Generator

UPLOAD_FOLDER = '/home/'
ALLOWED_EXTENSIONS = {'zip', 'json', 'kml'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def download(filename):
    uploads = os.path.join(current_app.root_path, '')
    return send_from_directory(directory=uploads, filename=filename, as_attachment=True)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path_save = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            path_out = os.path.join(app.config['UPLOAD_FOLDER'], os.path.splitext(filename)[0]+'.html')
            file.save(path_save)

            generator = Generator()
            generator.run([filename], path_out, [None, None], True, 'OpenStreetMap')

            os.remove(path_save)

            return redirect(url_for('download',
                                    filename=path_out.split('/')[-1]))
    return '''
    <!doctype html>
    <title>Geo Heatmap Generator</title>
    <h1>Geo Heatmap Generator</h1>
    <h2>Upload zip file from Google Maps History</h2>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 80)))