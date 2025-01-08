import pickle
import json
from langchain.docstore.document import Document

from BaseModels import RawIngredientList, ComplexIngredientList
from .Logger import Logger

logger = Logger()

# Object
def load_object_from_disk(path, object_name=None):
    """
    Load an object from the specified file path using pickle. Returns the deserialized object.
    """
    with open(path, "rb") as f:
        stored_object = pickle.load(f)
    logger.LogMessage(f"Object {object_name if object_name else ''} loaded from {path}")
    return stored_object

def store_object_on_disk(object_to_store, path, object_name=None):
    """
    store an object to the specified file path using pickle.
    """
    with open(path, "wb") as f:
        pickle.dump(object_to_store, f)
    logger.LogMessage(f"Object {object_name if object_name else ''} saved to {path}")


# Documents
def load_documents_from_disk(file_path:str) -> list[Document]:
    """
    Load documents from a JSON file, convert them to langchain Document objects, and return the list of documents.
    """
    serializable_docs = load_json_from_disk(file_path, "Documents")    
    # Convert to langchain Document objects
    documents = [Document(page_content=doc['page_content'], metadata=doc['metadata']) for doc in serializable_docs]    
    return documents

def store_documents_on_disk(documents:list[Document], file_path: str) -> None:
    """
    Store documents in a JSON file.
    """
    serializable_docs = [
        {
            'page_content': doc.page_content,
            'metadata': doc.metadata
        } for doc in documents
    ]
    # Write the documents to a JSON file
    store_json_on_disk(serializable_docs, file_path, "Documents")        

# RawIngredients
def store_raw_ingredient_lists_on_disk(obj_list: list[RawIngredientList], file_path: str):   
    """
    Convert a list of RawIngredientList objects to dictionaries and store them in a JSON file.
    """
    dict_list = [obj.model_dump() for obj in obj_list]
    store_json_on_disk(dict_list, file_path, "RawIngredientLists")    

def load_raw_ingredient_lists_from_disk(file_path: str) -> list[RawIngredientList]:  
    """
    Load a list of RawIngredientList objects from a JSON file.
    """  
    data = load_json_from_disk(file_path, "RawIngredientLists")    
    return [RawIngredientList(**item) for item in data]


# ComplexIngredients
def store_complex_ingredient_list_on_disk(obj_list: list[ComplexIngredientList], file_path: str) -> None:    
    """
    Convert a list of ComplexIngredientList objects to dictionaries and store them in a JSON file.
    """
    dict_list = [obj.model_dump() for obj in obj_list]        
    store_json_on_disk(dict_list, file_path, "ComplexIngredientLists")    

def load_complex_ingredient_list_from_disk(file_path: str) -> list[ComplexIngredientList]:
    """
    Load a list of ComplexIngredientList objects from a JSON file.
    """
    data = load_json_from_disk(file_path, "ComplexIngredientLists")  
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

# Json
def store_json_on_disk(obj, file_path, object_name: str = None):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    logger.LogMessage(f"Json object {object_name if object_name else ''} stored to {file_path}")
    
def load_json_from_disk(file_path, object_name: str = None):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.LogMessage(f"Json object {object_name if object_name else ''} loaded from {file_path}")
    return data