import pickle
import json
from langchain.docstore.document import Document

from BaseModels import RawIngredientList, ComplexIngredientList
from Logger import Logger

logger = Logger()

# Object
def load_object_from_disk(path):
    """Load the tokenizer from a file."""
    with open(path, "rb") as f:
        stored_object = pickle.load(f)
    logger.LogMessage(f"stored_object loaded from {path}")
    return stored_object

def store_object_on_disk(object_to_store, path):
    """Save the tokenizer to a file."""
    with open(path, "wb") as f:
        pickle.dump(object_to_store, f)
    logger.LogMessage(f"Object saved to {path}")


# Documents
def load_documents_from_disk(file_path:str) -> list[Document]:
    # Read the JSON file
    
    with open(file_path, 'r', encoding="utf-8") as f:
        serializable_docs = json.load(f)
    # Convert to langchain Document objects
    documents = [
        Document(page_content=doc['page_content'], metadata=doc['metadata'])
    for doc in serializable_docs]
    logger.LogMessage(f"Documents loaded from {file_path}")
    return documents

def store_documents_on_disk(documents:list[Document], file_path: str) -> None:
    serializable_docs = [
        {
            'page_content': doc.page_content,
            'metadata': doc.metadata
        } for doc in documents
    ]
    # Write the documents to a JSON file
    with open(file_path, 'w', encoding="utf-8") as f:
        json.dump(serializable_docs, f, ensure_ascii=False)
    logger.LogMessage(f"Documents saved to {file_path}")


# RawIngredients
def store_raw_ingredient_lists_on_disk(obj_list: list[RawIngredientList], file_path: str):   
    dict_list = [obj.dict() for obj in obj_list]
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(dict_list, f, ensure_ascii=False)  # Save as pretty-printed JSON
    logger.LogMessage(f"RawIngredientLists saved to {file_path}")

def load_raw_ingredient_lists_from_disk(file_path: str) -> list[RawIngredientList]:    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Convert the list of dictionaries to a list of RawIngredientList objects
    logger.LogMessage(f"RawIngredientLists loaded from {file_path}")    
    return [RawIngredientList(**item) for item in data]


# ComplexIngredients
def store_complex_ingredient_list_on_disk(obj_list: list[ComplexIngredientList], file_path: str) -> None:
    # Convert the Pydantic model to a dictionary
    dict_list = [obj.dict() for obj in obj_list]    
    # Write the dictionary as a JSON object to the file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(dict_list, f, ensure_ascii=False)
    logger.LogMessage(f"ComplexIngredientLists saved to {file_path}")

def load_complex_ingredient_list_from_disk(file_path: str) -> list[ComplexIngredientList]:
    # Read the JSON file
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Convert the dictionary back to a Pydantic model
    logger.LogMessage(f"ComplexIngredientLists loaded from {file_path}")    
    return [ComplexIngredientList(**item) for item in data]

# Text
def write_text_to_file(text:str, filename:str) -> None:
    """Schreibt den Text in eine Textdatei."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)    
    logger.LogMessage(f"Text saved to {filename}")

def read_text_from_file(filename:str) -> str:
    """Liest den Text aus einer Textdatei und gibt ihn zurück."""
    with open(filename, "r", encoding="utf-8") as file:
        text = file.read()    
    logger.LogMessage(f"{filename} loaded from disk")
    return text


    