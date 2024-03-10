from flask import Flask, render_template, request, redirect, url_for
from docx import Document
import PyPDF2
import os
import time  # Import the time module

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_to_txt(file_path):
    if file_path.lower().endswith('.pdf'):
        return convert_pdf_to_txt(file_path)
    elif file_path.lower().endswith(('.doc', '.docx')):
        return convert_doc_to_txt(file_path)


def convert_pdf_to_txt(file_path):
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ''
        for page_num in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page_num)
            text += page.extractText()
    return text


def convert_doc_to_txt(file_path):
    doc = Document(file_path)
    text = ''
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'
    return text


@app.route('/')
def index():
    alert = request.args.get('alert')  # Get alert parameter from query string
    return render_template('index.html', alert=alert)


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part'

    files = request.files.getlist('file')
    upload_folder = app.config['UPLOAD_FOLDER']

    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    for file in files:
        if file and allowed_file(file.filename):
            filename = os.path.join(upload_folder, file.filename)
            file.save(filename)
            txt_content = convert_to_txt(filename)
            txt_filename = os.path.join(upload_folder, os.path.splitext(file.filename)[0] + '.txt')
            with open(txt_filename, 'w', encoding='utf-8') as txt_file:
                txt_file.write(txt_content)

    # Add a small delay before redirecting
    time.sleep(1)

    return redirect(url_for('index', alert='Files uploaded and converted successfully!'))


if __name__ == '__main__':
    app.run(debug=True)
