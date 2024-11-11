from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from typing import List, Tuple
import chromadb 



class VectorStore:
    def __init__(self) -> None:        
        self.embeddings = OllamaEmbeddings(model="mxbai-embed-large") 
        self.db_path:str = 'Receipes/Chroma'
        self.chroma_db = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)        
        self.documents_and_scores : List[Tuple[Document, float]] = []
        self.last_selected_source:str = ""

    def get_chromaDB(self) -> Chroma:
        return Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)


    def retrieve_receipe_info(self, query:str)->List[str]:
        """ Retrieves receipe info and stores current retrieval results"""
        self.documents_and_scores = self.chroma_db.similarity_search_with_score(query=query, k=10)

        receipes = []
        for document, score in self.documents_and_scores:
            receipes.append(document.page_content)
        return receipes
    
    def get_receipe_List(self, index:int)->Tuple[List[str], str]:
        """
        get the receipe with the given index from the current retrieval results.
        Retrieve all receipes with the same metadata from the database and return them as a list
        """
        # todo: if docstore empty, return a corresponding message
        selected_receipe = self.documents_and_scores[int(index)]
        

        # Define the metadata filter
        metadata_key = "source"  # Replace with the actual metadata key you're filtering by
        self.last_selected_source = selected_receipe[0].metadata[metadata_key]
        source = self.last_selected_source.split("\\")[-1]
                                                             
        return self.get_receipes_from_last_source(), source
    
    def get_receipes_from_last_source(self)->List[str]:
        """get all receipes strings from the last selected source"""
        collection = self.chroma_db.get(
            where={"source": self.last_selected_source},
            include=["documents"]
            )
        return collection["documents"]
    
    def get_last_selected_source(self)->str:
        return self.last_selected_source