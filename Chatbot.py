from ast import Dict
from langchain_core.output_parsers import StrOutputParser 
from operator import itemgetter
from langchain_core.prompts import PromptTemplate
from typing import List, Union
from langchain_core.runnables import RunnableLambda, RunnableAssign, RunnableBranch
import pandas as pd
import concurrent.futures
import threading
from VectorStore import VectorStore


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
    def __init__(self, model, vector_store: VectorStore):
        self.model = model
        self.vector_store = vector_store
       
    
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
            (lambda state: state['message'].startswith('retrieval:'), lambda state: self.allReceipesOfThisWeek(state)),
            (lambda state: state['message'].startswith('soppinglist:'), lambda state: self.createShoppingList(state)),            
            lambda state: self.chat_bot(state)
        )
        for token in branch.stream(state):
            yield token
                                 
  
    def chat_bot(self, state):
        """ standard chatbot with 5 message history """
        systemmessage = '''        
            <|begin_of_text|>
            <|start_header_id|>system<|end_header_id|>
            Du bist ein Freundlicher Koch, der sich am liebsten ueber Essen unterhaelt. Du redest aber auch gern ueber jedes andere Thema.          
            <|eot_id|>
            '''

        historystring = self.build_history(state['history'][-5:])
        prompt = PromptTemplate.from_template(f"{systemmessage}{historystring}" + "<|start_header_id|>user<|end_header_id|>{input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>")
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
    
    def allReceipesOfThisWeek(self, state: Dict)->str:
        """retrieve a list of receipe names from the json file based on the metadata"""
        currentReceipeSelectionIndex = state['message'].split(":")[1]                        
        # retrieve a list of receipes with the same metadata
        receipeList, source = self.vector_store.get_receipe_List(currentReceipeSelectionIndex)
        
        joined_receipes = "\n\n".join(receipeList)
        joined_receipes += f"\n\nSource: {source}"
        return joined_receipes
    
    def createShoppingList(self, state):
        """create a shopping list based on the selected receipes"""
        json_data = state['message'].split("soppinglist:")[1]
        df_restored = pd.read_json(json_data, orient="split")
        
        # List_of_mapped_receipes = mapping_function(state['pd dataframe'], Ingredient_List) -> llm
        # count all receipes
        # List with receipenames and complex ingredients -> llm
        # multiply all ingredients
        # bundle all ingredients and add to list -> list: external, mapping: llm

        pass
    
    def myCoolMappingfunction(self, shortList, longList)->:
        """mapping function for the ingredients of the receipes"""
        pass