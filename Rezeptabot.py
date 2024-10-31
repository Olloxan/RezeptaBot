from langchain_community.llms import Ollama
from UserInterface import UserInterface
from VectorStore import VectorStore
from Chatbot import ChatbotWithHistory


vector_store = VectorStore()

modelname = "llama3.1:8b-instruct-q4_K_S"
model = Ollama(model = modelname)
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
    

def document_retrieve(text_input):    
    receipe_info = vector_store.retrieve_receipe_info(query=text_input)
    return receipe_info

                               

    # for token in model.stream(message):        
    # ## If you're using standard print, keep line from getting too long
    #     buffer += token
    #     yield buffer

# test_question = "Tell me about RAG!"  ## <- modify as desired       
# for response in chat_gen(test_question, return_buffer=False):
#     print(response, end='')

interface = UserInterface(chat_fn=chat_gen, doc_retrieval_fn=document_retrieve)
interface.render()


