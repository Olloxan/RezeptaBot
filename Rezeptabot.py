from langchain_community.llms import Ollama
from UserInterface import UserInterface
from VectorStore import VectorStore
from Chatbot import ChatbotWithHistory

from langchain_core.runnables import RunnableLambda, RunnableAssign, RunnableBranch

modelname = "llama3.1:8b-instruct-q4_K_S"
model = Ollama(model = modelname)
chatbot = ChatbotWithHistory(model=model)
chatbot.preloadModel()

vector_store = VectorStore()
chroma_db = vector_store.get_chromaDB()

# branch = RunnableBranch(
#     default= model,  # Default chain to run
#     branches={
#         "collect_info": model,
#         "process_info": model,
#         "provide_summary": model,
#     },
#     select_branch=lambda inputs: state_machine.get_state()  # Dynamic state selection
#     )

state = {}
def chat_gen(message, history=[], return_buffer=True):        
    buffer = "" 
            
    state['message'] = message
    state['history'] = history
    for token in chatbot.stream(state):           
        buffer += token
        yield buffer if return_buffer else token
    

def document_retrieve(text_input):
    
    docs_and_scores = chroma_db.similarity_search_with_score(query=text_input, k=10)

    receipes = []
    for doc, score in docs_and_scores:
        receipes.append(doc.page_content)
        
    return receipes
        
    
    
     

    # for token in model.stream(message):        
    # ## If you're using standard print, keep line from getting too long
    #     buffer += token
    #     yield buffer

# test_question = "Tell me about RAG!"  ## <- modify as desired       
# for response in chat_gen(test_question, return_buffer=False):
#     print(response, end='')

interface = UserInterface(chat_fn=chat_gen, doc_retrieval_fn=document_retrieve)
interface.render()


