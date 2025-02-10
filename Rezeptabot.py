from langchain_ollama import OllamaLLM
from UserInterface import UserInterface
from VectorStore import VectorStore
from Chatbot import ChatbotWithHistory


vector_store = VectorStore(collection_name='recipe_embeddings')

modelname = "llama3.1:8b-instruct-q8_0"
model = OllamaLLM(model = modelname)
chatbot = ChatbotWithHistory(model=model, vector_store=vector_store)
chatbot.preloadModel()

state = {}

def chat_gen(message, history=[], return_buffer=True):        
    # state['message'] = user message: str
    # state['history'] = history: [[(user) None, (agent) "Hello you!"]] (List of Lists)
    
    buffer = ""             
    state['message'] = message
    state['history'] = history
    for token in chatbot.stream(state):           
        buffer += token
        yield buffer if return_buffer else token
    

def document_retrieve(text_input)->list[str]:    
    receipe_info = vector_store.retrieve_receipe_info(query=text_input)
    return receipe_info

                               

interface = UserInterface(chat_fn=chat_gen, doc_retrieval_fn=document_retrieve)
interface.render()


