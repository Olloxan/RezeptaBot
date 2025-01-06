from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from typing import Tuple
from Logger import Logger


class VectorStore:
    def __init__(self, db_persist_path='Recipes/Chroma', collection_name="langchain") -> None:        
        self.embeddings = OllamaEmbeddings(model="mxbai-embed-large") 
        self.db_path:str = db_persist_path
        self.collection_name:str = collection_name
        self.chroma_db = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings, collection_name=self.collection_name)        
        self.documents_and_scores : list[Tuple[Document, float]] = []
        self.last_selected_source:str = ""
        self.logger = Logger()

    def get_chromaDB(self) -> Chroma:
        return Chroma(persist_directory=self.db_path, embedding_function=self.embeddings, collection_name=self.collection_name)


    def retrieve_receipe_info(self, query:str)->list[Tuple[str, float]]:
        """ Retrieves recipe info and stores current retrieval results"""        
        self.documents_and_scores = self.chroma_db.similarity_search_with_score(query=query, k=10)

        self.documents_and_scores = sorted(self.documents_and_scores, key=lambda x: x[1], reverse=True)
                          
        if(len(self.documents_and_scores) == 0):
            self.LogException(Exception(f"Something went wrong with the vecor store. Check path: {self.db_path}, Collectionname: {self.collection_name}"))

        self.LogMessage(f"Retried {len(self.documents_and_scores)} recipes for query: {query}")
        
        return [(doc.page_content, round(score, 2)) for doc, score in self.documents_and_scores]
    
    def get_receipe_List(self, index:int)->Tuple[list[str], str]:
        """
        get the receipe with the given index from the current retrieval results.
        Retrieve all recipes with the same metadata from the database and return them as a list
        """
        # todo: if docstore empty, return a corresponding message
        source = "Something went wrong"
        try:
            selected_receipe = self.documents_and_scores[int(index)]                
            # Define the metadata filter
            metadata_key = "source"  # Replace with the actual metadata key you're filtering by
            self.set_source( selected_receipe[0].metadata[metadata_key])
            source = self.get_last_selected_source().split("\\")[-1]
        except Exception as exc:                                                 
            self.LogException(exc)
            
        return self.get_recipes_from_last_source(), source
    
    def get_recipes_from_last_source(self)->list[str]:
        """get all reciipes strings from the last selected source"""
        collection = self.chroma_db.get(
            where={"source": self.get_last_selected_source()},
            include=["documents"]
            )
        return collection["documents"]
    
    def get_last_selected_source(self)->str:
        self.LogMessage(f"Returning last selected source: {self.last_selected_source}")
        return self.last_selected_source
    
    def set_source(self, source:str):
        self.last_selected_source = source
        self.LogMessage(f"Setting source to: {source}")

    def LogMessage(self, message:str):
        self.logger.LogMessage(message, self)
        
    def LogException(self, exception:Exception, message:str = "Processing failed"):
        self.logger.LogException(exception, message, self)