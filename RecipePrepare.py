import json
from langchain.docstore.document import Document
from Utils import load_documents_from_disk


pages = load_documents_from_disk('Receipes/AllNewRecipes.json')

print(len(pages))


