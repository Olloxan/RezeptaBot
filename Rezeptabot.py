import stat
from langchain_community.llms import Ollama
from UserInterface import UserInterface
from VectorStore import VectorStore
from Chatbot import ChatbotWithHistory

modelname = "llama3.1:8b-instruct-q4_K_S"
model = Ollama(model = modelname)


vector_store = VectorStore()
chroma_db = vector_store.get_chromaDB()

chatbot = ChatbotWithHistory(model=model)

conversation_state = 0


def chat_gen(message, history=[], return_buffer=True):        
    buffer = "" 
    #### ToDo ####
    if conversation_state == 0:
        
    # State 0: 
    # Plauerphase: das Netzwerk unterhaelt sich mit dem Nutzer (ein kurzes Lebenszeichen, um zu sehen, ob Ollama laeuft, Ollama aus einem Subprocess heraus starten, wenn es nicht schon laeuft)    
        state={'message' : message}
        state['history'] = history
        for token in chatbot.stream(state):           
            buffer += token
            yield buffer if return_buffer else token

    elif state == 1:
    # state 1: 
        # docs_and_scores = chroma_db.similarity_search_with_score(query=message, k=20)

        # for doc, score in docs_and_scores:
        #     buffer += f"Document: {doc}, Similarity Score: {score}\n"
        #     yield buffer
        x=3
    # state 2: Einkaufsliste
       

    # for token in model.stream(message):        
    # ## If you're using standard print, keep line from getting too long
    #     buffer += token
    #     yield buffer

# test_question = "Tell me about RAG!"  ## <- modify as desired       
# for response in chat_gen(test_question, return_buffer=False):
#     print(response, end='')

interface = UserInterface(chatfunction=chat_gen)
interface.render()


