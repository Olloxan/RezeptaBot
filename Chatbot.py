from langchain_core.output_parsers import StrOutputParser 
from operator import itemgetter
from langchain_core.prompts import PromptTemplate
from typing import List, Union

from langchain_core.runnables import RunnableLambda, RunnableAssign
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
            Du bist ein Freundlicher Koch, der sich ueber Essen unterhalten moechte.
            Wenn die Nutzerin ein Rezept sucht, schreibe Strumpfhose in deine Antwort
            <|eot_id|>
            '''
        

    def stream(self, state: dict):
        # state['message'] = user message: str
        # state['history'] = history: [[(user) None, (agent) "Hello you!"]] (List of Lists)
        historystring = self.build_history(state['history'][-5:])
        prompt = PromptTemplate.from_template(f"{self.systemmessage}{historystring}" + "<|start_header_id|>user<|end_header_id|>{input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>")
        parser = StrOutputParser()
                        
        chain = (            
            { 
                "input": itemgetter("message") 
            }             
            | prompt            
            | self.model                                  
            | parser
            )
                
        for token in chain.stream(state):                       
            yield token


    def build_history(self, history: List[List[Union[None, str]]]) -> str:              
        prompt = ""
        for messages in history:            
            usermessage, agentmessage = messages
            prompt += f"<|start_header_id|>user<|end_header_id|>{usermessage}<|eot_id|><|start_header_id|>assistant<|end_header_id|>{agentmessage}<|eot_id|>"            
        return prompt
            
  