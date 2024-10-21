from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma


class VectorStore:
    def __init__(self) -> None:        
        self.embeddings = OllamaEmbeddings(model="mxbai-embed-large") 
        self.db_path = 'Receipes'
        
        
    def get_chromaDB(self) -> Chroma:
        return Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)
