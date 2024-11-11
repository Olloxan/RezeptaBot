import json
from langchain.docstore.document import Document

class FileLoader():
    def __init__(self) -> None:
        self.directory = "Receipes/Prompts/"
        pass
    
    def read_from_file(self, filename:str) -> str:        
        with open(self.directory + filename, "r", encoding="utf-8") as file:
            text = file.read()
        print(f"Text aus {filename} geladen.")
        return text
    
    def load_documents_from_disk(self, file_path):
        # Read the JSON file
        with open(file_path, 'r') as f:
            serializable_docs = json.load(f)
        # Convert to langchain Document objects
        documents = [
            Document(page_content=doc['page_content'], metadata=doc['metadata'])
        for doc in serializable_docs]
        return documents
