from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from PIL import Image
import numpy as np
import os
import uuid

app = Flask(__name__)
app.secret_key = "your_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(img_path, key, mode):
    img = Image.open(img_path)
    img_array = np.array(img).astype(np.uint16)  # prevent overflow

    if mode == 'xor':
        result_array = img_array ^ key
    elif mode == 'add':
        result_array = (img_array + key) % 256
    elif mode == 'multiply':
        result_array = (img_array * key) % 256
    else:
        result_array = img_array

    result_array = result_array.astype(np.uint8)
    result_img = Image.fromarray(result_array)

    result_filename = f"{uuid.uuid4().hex}_result.png"
    result_path = os.path.join(UPLOAD_FOLDER, result_filename)
    result_img.save(result_path)
    return result_filename

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash("No file uploaded.")
            return redirect(request.url)

        image = request.files['image']
        if image.filename == '':
            flash("No file selected.")
            return redirect(request.url)

        if not allowed_file(image.filename):
            flash("Unsupported file type. Use PNG, JPG or JPEG.")
            return redirect(request.url)

        try:
            key = int(request.form['key'])
            if not (1 <= key <= 255):
                flash("Key must be between 1 and 255.")
                return redirect(request.url)
        except ValueError:
            flash("Invalid key entered.")
            return redirect(request.url)

        mode = request.form['mode']

        original_filename = f"{uuid.uuid4().hex}_{image.filename}"
        image_path = os.path.join(UPLOAD_FOLDER, original_filename)
        image.save(image_path)

        result_filename = process_image(image_path, key, mode)

        return render_template('result.html',
                               original_image=url_for('uploaded_file', filename=original_filename),
                               result_image=url_for('uploaded_file', filename=result_filename),
                               result_filename=result_filename)

    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=False)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
