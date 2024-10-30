from xxlimited import foo
from langchain_core.output_parsers import StrOutputParser 
from operator import itemgetter
from langchain_core.prompts import PromptTemplate
from typing import List, Union
from langchain_core.runnables import RunnableLambda, RunnableAssign, RunnableBranch
import concurrent.futures
import threading


from functools import partial
from rich.console import Console
from rich.style import Style
from rich.theme import Theme

console = Console()
base_style = Style(color="#76B900", bold=True)
pprint = partial(console.print, style=base_style)

def PrintTextWithLabel(label="State: "):
    def print_and_return(x, label=""):
        print(f"{label}{x}")
        return x
    return RunnableLambda(partial(print_and_return, label=label))

def PrintStructureWithLabel(preface="State: "):
    def print_and_return(x, preface=""):
        pprint(preface, x)
        return x
    return RunnableLambda(partial(print_and_return, preface=preface))

class ChatbotWithHistory:
    def __init__(self, model):
        self.model = model
        self.systemmessage = '''        
            <|begin_of_text|>
            <|start_header_id|>system<|end_header_id|>
            Du bist ein Freundlicher Koch, der sich am liebsten ueber Essen unterhaelt. Du redest aber auch gern ueber jedes andere Thema.          
            <|eot_id|>
            '''
    
    def preloadModel(self):
        self.startup()
        
    def startup(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(self.load_model)
        
    def load_model(self):
        print("Loading model")
        self.model.invoke("")
        print("model loaded")
    
    def stream(self, state: dict):
        # state['message'] = user message: str
        # state['history'] = history: [[(user) None, (agent) "Hello you!"]] (List of Lists)
        
        branch = RunnableBranch(
            #(condition, runnable)
            (lambda x: x['message'].startswith('retrieval:'), lambda x: x.upper()),
            (lambda x: x['message'].startswith('soppinglist:'), lambda x: x + 1),            
            lambda x: self.chat_bot(x)
        )
        for token in branch.stream(state):
            yield token

        # branch = RunnableBranch(   
        #     branches={
        #         "chatbot": model,
        #         "retrieval": model,
        #         "soppinglist": model,
        #     },
        #     select_branch=lambda inputs: state_machine.get_state()  # Dynamic state selection
       
        




        # state['message'] = user message: str
        # state['history'] = history: [[(user) None, (agent) "Hello you!"]] (List of Lists)
        
  
    def chat_bot(self, state):
        """ standard chatbot with 5 message history """
        historystring = self.build_history(state['history'][-5:])
        prompt = PromptTemplate.from_template(f"{self.systemmessage}{historystring}" + "<|start_header_id|>user<|end_header_id|>{input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>")
        parser = StrOutputParser()
                        
        return (            
            { 
                "input": itemgetter("message") 
            }             
            | prompt            
            | self.model                                  
            | parser
            )
    
    def build_history(self, history: List[List[Union[None, str]]]) -> str:              
        prompt = ""
        for messages in history:            
            usermessage, agentmessage = messages
            prompt += f"<|start_header_id|>user<|end_header_id|>{usermessage}<|eot_id|><|start_header_id|>assistant<|end_header_id|>{agentmessage}<|eot_id|>"            
        return prompt