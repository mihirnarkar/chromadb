import chromadb
import psycopg2
from psycopg2 import sql


client = chromadb.Client()

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


file_data = read_files_from_database()


documents = []
metadatas = []
ids = []

for index, data in enumerate(file_data):
    documents.append(data['content'])
    metadatas.append({'source': data['file_name']})
    ids.append(str(index + 1))

collection = client.create_collection("mycollection2")

collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

while(True):
    userquery = input("Enter your query: ")
    results = collection.query(
        query_texts = [userquery],
        n_results=2
    )

    print(f"Results : {results}")
    print("")
    print("")
    print("")
    print("")
    print("")
    print("")




