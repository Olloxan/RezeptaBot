
from langchain_core.output_parsers import StrOutputParser 
from operator import itemgetter
from langchain_core.prompts import PromptTemplate
from typing import Counter, List, Union, Dict
from langchain_core.runnables import RunnableLambda, RunnableAssign, RunnableBranch
import pandas as pd
import concurrent.futures
import threading
from VectorStore import VectorStore
from Promptloader import Promptloader

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
        self.promptloader = Promptloader()
       
    
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
            (lambda state: state['message'].startswith('shoppinglist:'), lambda state: self.createShoppingList(state)),            
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
        
        # restore pandas dataframe from json
        json_data = state['message'].split("shoppinglist:")[1]
        df_restored = pd.read_json(json_data, orient="split")
        
        # get list of receipe names from vector store
        receipes_and_ingredients = self.vector_store.get_receipes_from_last_source()

        # List_of_mapped_receipes = mapping_function(state['pd dataframe'], Ingredient_List) -> llm
        meals = self.receipe_name_mapping(df_restored, receipes_and_ingredients)
                
        # count all receipes
        mealcount = Counter(meals)
        
        # List with receipenames and complex ingredients -> llm
        # multiply all ingredients
        # bundle all ingredients and add to list -> list: external, mapping: llm
        # Ich will nen Looger
        
        pass
    
    def receipe_name_mapping(self, short_receipe_names:pd.DataFrame, receipe_name_list:List[str])->List[str]:
        """assignes each entry of the short_name_list the corresponding complete receipe name
           e.g. curry -> Kokosnuss Curry Eintopf mit Tofu
        """        
        
        # 02.08.2024-3400kcal.pdf
        # Schoko-Smoothie mit Beeren
        prompt = PromptTemplate.from_template(self.promptloader.read_from_file("ReceipeNameMapping.txt"))                
        
        parser = StrOutputParser()                
        chain = (
            {
                "short_name_list" : itemgetter("short_name_list"),
                "full_receipe_names" : itemgetter("full_receipe_names")
            }
            | prompt            
            | self.model            
            | parser
        )
        
        full_name_list:List[str] = [name.split(" - Ingredients")[0].strip() for name in receipe_name_list]
        full_receipe_names = "; ".join(full_name_list)
        
        # Morgens, Mittags, Abends, Nachmittags 
        mealtimes = ["Morgens", "Mittags", "Abends", "Nachmittags"]
        meals = []
        for mealtime in mealtimes:            
            short_name_list = [item for item in short_receipe_names[mealtime] if item != ""]
            short_name_list_string = "; ".join(short_name_list)
            counter = 0
            while(True):
                print(f"running loop with {mealtime} for the {counter}th time")
                
                output = chain.invoke({"short_name_list" : short_name_list_string, "full_receipe_names" : full_receipe_names})
                
                output_list:List[str] = self.clean_string_and_convert_to_list(output)
                if self.output_conditions_are_met(output_list, short_name_list, full_name_list):                
                    break
                counter += 1
            meals.extend(output_list)
        return meals
    
    def clean_string_and_convert_to_list(self, string:str)->List[str]:                 
        string = (string
                  .replace("\n", "")
                  .replace(".", "")
                  )
        output_list = [item.strip() for item in string.split(";")]
        return output_list
    
    def output_conditions_are_met(self, output_list:List[str], short_name_list:List[str], full_name_list:List[str])->bool:
        """Output conditions: 
            1. is the output list a subset of the full name list
            2. have the output list and the list of short names the same length            
        """
        conditions:List[bool] = []
        conditions.append(set(output_list).issubset(set(full_name_list)))
        missing_elements = set(output_list) - set(full_name_list)
        print(f"missing elements: {missing_elements}")
        debuglen1 = len(output_list)
        debuglen2 = len(short_name_list)
        print(f"length list1: {debuglen1}")
        print(f"length list2: {debuglen2}")
        conditions.append(len(output_list) == len(short_name_list))                            
        return all(conditions)