import os
import chromadb

client = chromadb.Client()

def read_files_from_folder(folder_path):
    file_data = []

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".txt"):
            with open(os.path.join(folder_path, file_name), 'r') as file:
                content = file.read()
                file_data.append({"file_name": file_name, "content": content})

    return file_data

folder_path = "D:\\chromadb\\uploads"
file_data = read_files_from_folder(folder_path)


documents = []
metadatas = []
ids = []

for index, data in enumerate(file_data):
    documents.append(data['content'])
    metadatas.append({'source': data['file_name']})
    ids.append(str(index + 1))

collection = client.create_collection("mycollection")

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




