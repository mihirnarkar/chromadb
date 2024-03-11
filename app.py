from flask import Flask, render_template, request, redirect, url_for
from docx import Document
import PyPDF2
import os
import psycopg2
from psycopg2 import sql
import chromadb

app = Flask(__name__)

# PostgreSQL database configuration
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_USER = 'postgres'
DB_PASSWORD = 'root'
DB_NAME = 'chromadb'
TABLE_NAME = 'uploads'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

client = chromadb.Client()

collection_index = 0


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


def store_in_database(file_content, file_name):
    connection = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, database=DB_NAME
    )

    cursor = connection.cursor()

    # Create table if not exists
    create_table_query = sql.SQL("""
        CREATE TABLE IF NOT EXISTS {table} (
            id SERIAL PRIMARY KEY,
            content TEXT,
            source VARCHAR(255)
        );
    """).format(table=sql.Identifier(TABLE_NAME))

    cursor.execute(create_table_query)

    # Insert data into the database
    insert_query = sql.SQL("INSERT INTO {table} (content, source) VALUES ({}, {});").format(
        sql.Literal(file_content), sql.Literal(file_name),
        table=sql.Identifier(TABLE_NAME)
    )

    cursor.execute(insert_query)

    # Commit changes and close the connection
    connection.commit()
    connection.close()


def read_files_from_database():
    file_data = []

    connection = psycopg2.connect(
        host='localhost', port='5432',
        user='postgres', password='root',
        database='chromadb'
    )

    cursor = connection.cursor()

    # Fetch data from the database
    select_query = sql.SQL("SELECT * FROM uploads;")
    cursor.execute(select_query)
    rows = cursor.fetchall()

    for row in rows:
        file_data.append({"file_name": row[2], "content": row[1]})

    # Close the connection
    connection.close()

    return file_data


@app.route('/')
def index():
    alert = request.args.get('alert')  # Get alert parameter from the query string
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
            txt_filename = os.path.splitext(file.filename)[0] + '.txt'
            store_in_database(txt_content, txt_filename)

    return redirect(url_for('index', alert='Files uploaded and converted successfully!'))


@app.route('/submit', methods=['GET'])
def submit():
    global collection_index  # Declare the variable as global
    user_query = request.args.get('query')

    # Perform the query and get the results from ChromaDB
    documents = []
    metadatas = []
    ids = []

    file_data = read_files_from_database()

    collection_index += 1

    for index, data in enumerate(file_data):
        documents.append(data['content'])
        metadatas.append({'source': data['file_name']})
        ids.append(str(index + 1))

    collection_name = f"mycollection{collection_index}"

    collection = client.create_collection(collection_name)

    # collection = client.create_collection(f"mycollection{collection_index}")

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    results = collection.query(
        query_texts=[user_query],
        n_results=2
    )

    return f"Results: {results}"


if __name__ == '__main__':
    app.run(debug=True)
