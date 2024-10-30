from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from typing import List, Tuple




class VectorStore:
    def __init__(self) -> None:        
        self.embeddings = OllamaEmbeddings(model="mxbai-embed-large") 
        self.db_path = 'Receipes'
        self.chroma_db = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)        
        self.documents_and_scores : List[Tuple[Document, float]] = []

    def get_chromaDB(self) -> Chroma:
        return Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)


    def retrieve_receipe_info(self, query:str)->List[str]:
        """ Retrieves receipe info and stores current retrieval results"""
        self.documents_and_scores = self.chroma_db.similarity_search_with_score(query=query, k=10)

        receipes = []
        for document, score in self.documents_and_scores:
            receipes.append(document.page_content)
        return receipes