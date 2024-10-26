import stat
from langchain_community.llms import Ollama
from UserInterface import UserInterface
from VectorStore import VectorStore
from Chatbot import ChatbotWithHistory


from langchain_core.runnables import RunnableLambda, RunnableAssign, RunnableBranch

modelname = "llama3.1:8b-instruct-q4_K_S"
model = Ollama(model = modelname)


vector_store = VectorStore()
chroma_db = vector_store.get_chromaDB()

chatbot = ChatbotWithHistory(model=model)

conversation_state = 0

state = {}

class ConversationStateMachine:
    def __init__(self):
        self.state = "collect_info"  # Initial state
    

    def update_state(self, model_output):
        # ich will, dass hier einfach nur das state_dict rein geht und der state raus geholt wird
        if "enough information" in model_output.lower():
            self.state = "process_info"
        elif "processing complete" in model_output.lower():
            self.state = "provide_summary"
        # Add more complex logic as needed
    
    def get_state(self):
        return self.state

state_machine = ConversationStateMachine()

branch = RunnableBranch(
    default= model,  # Default chain to run
    branches={
        "collect_info": model,
        "process_info": model,
        "provide_summary": model,
    },
    select_branch=lambda inputs: state_machine.get_state()  # Dynamic state selection
    )

def chat_gen(message, history=[], return_buffer=True):        
    buffer = "" 
    
    output = branch.invoke(state)
    streamoutput = output['answer']
    for token in streamoutput:            
        buffer += token
        yield buffer
    
    #### ToDo ####
    
     

    # for token in model.stream(message):        
    # ## If you're using standard print, keep line from getting too long
    #     buffer += token
    #     yield buffer

# test_question = "Tell me about RAG!"  ## <- modify as desired       
# for response in chat_gen(test_question, return_buffer=False):
#     print(response, end='')

interface = UserInterface(chatfunction=chat_gen)
interface.render()


