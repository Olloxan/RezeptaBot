from huggingface_hub import User

from langchain_community.llms import Ollama
from UserInterface import UserInterface
from VectorStore import VectorStore
modelname = "llama3.1:8b-instruct-q4_K_S"

model = Ollama(model = modelname)


vector_store = VectorStore()
chroma_db = vector_store.get_chromaDB()

def chat_gen(message, history):        
    buffer = "" 
    #### ToDo ####
    # State 0: 
    # Plauerphase: das Netzwerk unterhaelt sich mit dem Nutzer (ein kurzes Lebenszeichen, um zu sehen, ob Ollama laeuft, Ollama aus einem Subprocess heraus starten, wenn es nicht schon laeuft)
    
    # state 1: 
    docs_and_scores = chroma_db.similarity_search_with_score(query=message, k=20)

    for doc, score in docs_and_scores:
        buffer += f"Document: {doc}, Similarity Score: {score}\n"
        yield buffer
    
    # state 2: Einkaufsliste
    
     
     
    for token in model.stream(message):        
    ## If you're using standard print, keep line from getting too long
        buffer += token
        yield buffer
        
interface = UserInterface(chatfunction=chat_gen)
interface.render()


