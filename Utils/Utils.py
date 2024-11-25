import pickle
import json
from langchain.docstore.document import Document
from typing import List

from BaseModels import RawIngredientList

# Load Structure from file
def load_object(path):
    """Load the tokenizer from a file."""
    with open(path, "rb") as f:
        stored_object = pickle.load(f)
    print(f"stored_object loaded from {path}")
    return stored_object

# Safe Structure to file
def save_object(object_to_store, path):
    """Save the tokenizer to a file."""
    with open(path, "wb") as f:
        pickle.dump(object_to_store, f)
    print(f"Tokenizer saved to {path}")

# Load documents from file
def load_documents_from_disk(file_path:str) -> List[Document]:
    # Read the JSON file
    with open(file_path, 'r', encoding="utf-8") as f:
        serializable_docs = json.load(f)
    # Convert to langchain Document objects
    documents = [
        Document(page_content=doc['page_content'], metadata=doc['metadata'])
    for doc in serializable_docs]
    return documents

# Store documents in file
def store_documents_on_disk(documents:List[Document], file_path: str) -> None:
    serializable_docs = [
        {
            'page_content': doc.page_content,
            'metadata': doc.metadata
        } for doc in documents
    ]
    # Write the documents to a JSON file
    with open(file_path, 'w', encoding="utf-8") as f:
        json.dump(serializable_docs, f)

# Function to save a list of RawIngredientList objects as JSON
def store_raw_ingredient_lists_on_disk(obj_list: List[RawIngredientList], file_path: str):   
    dict_list = [obj.dict() for obj in obj_list]
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(dict_list, file, ensure_ascii=False)  # Save as pretty-printed JSON

# Function to load JSON and populate a list of RawIngredientList objects
def load_raw_ingredient_lists_from_disk(file_path: str) -> List[RawIngredientList]:    
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    # Convert the list of dictionaries to a list of RawIngredientList objects
    return [RawIngredientList(**item) for item in data]





# Store text in file
def write_to_file(text:str, filename:str) -> None:
    """Schreibt den Text in eine Textdatei."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write(text)
    print(f"Text wurde in {filename} gespeichert.")

# Read text from file
def read_from_file(filename:str) -> str:
    """Liest den Text aus einer Textdatei und gibt ihn zurück."""
    with open(filename, "r", encoding="utf-8") as file:
        text = file.read()
    print(f"Text aus {filename} geladen.")
    return text