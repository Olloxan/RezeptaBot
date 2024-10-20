from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama


modelname = "llama3.1:8b-instruct-q4_K_S"

model = Ollama(model = modelname)


embedding_modelname = "mxbai-embed-large"
embeddings = OllamaEmbeddings(model=embedding_modelname) 

db_path = 'Receipes'
vector_store = Chroma(persist_directory=db_path, embedding_function=embeddings)

def chat_gen(message, history):
    buffer = "" 
    docs_and_scores = vector_store.similarity_search_with_score(query=message, k=20)

    for doc, score in docs_and_scores:
        buffer += f"Document: {doc}, Similarity Score: {score}\n"
        yield buffer
    
    
     
     
    # for token in model.stream(message):        
    # ## If you're using standard print, keep line from getting too long
    #     buffer += token
    #     yield buffer
        





