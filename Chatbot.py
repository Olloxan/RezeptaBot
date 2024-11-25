
from langchain_core.output_parsers import StrOutputParser 
from operator import itemgetter
from langchain_core.prompts import PromptTemplate
from typing import Counter, List, Union, Dict
from langchain_core.runnables import RunnableLambda, RunnableAssign, RunnableBranch
from langchain.docstore.document import Document
from numpy import promote_types
import pandas as pd
import concurrent.futures
import threading
from Runnables import RunnableComplexIngredientExtractor, RunnableRawIngredientExtracor, RunnableRecipeMapper
from VectorStore import VectorStore
from FileLoader import FileLoader
from BaseModels import RawIngredientList, ComplexIngredientList

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
        self.loader = FileLoader()
       
    
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
                                 
    ################################ Chatbot ################################
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
    
    ################################ retrieval ################################
    def allReceipesOfThisWeek(self, state: Dict)->str:
        """retrieve a list of receipe names from the json file based on the metadata"""
        currentReceipeSelectionIndex = state['message'].split(":")[1]                        
        # retrieve a list of receipes with the same metadata
        receipeList, source = self.vector_store.get_receipe_List(currentReceipeSelectionIndex)
        
        joined_receipes = "\n\n".join(receipeList)
        joined_receipes += f"\n\nSource: {source}"
        return joined_receipes
    
    ################################ shoppinglist ################################
    def createShoppingList(self, state):
        """create a shopping list based on the selected receipes"""
        
        # restore pandas dataframe from json
        json_data = state['message'].split("shoppinglist:")[1]
        df_restored = pd.read_json(json_data, orient="split")
        
        # get list of receipe names from vector store
        receipes_and_ingredients = self.vector_store.get_receipes_from_last_source()

        # List_of_mapped_receipes = mapping_function(state['pd dataframe'], Ingredient_List) -> llm
        prompt = PromptTemplate.from_template(self.loader.read_from_file("ReceipeNameMapping.txt"))
        recipeMapper = RunnableRecipeMapper(self.model, prompt)
        
        state={}
        state['short_recipe_names'] = df_restored
        state['recipe_names_with_ingredients'] = receipes_and_ingredients 
        output = recipeMapper.invoke(state)
        
                
        # count all receipes -> Dict with receipenames as Key and count as value
        mealcount = Counter(output)
        
        # Load all receipes from json with the corresponding source
        all_receipes = self.loader.load_documents_from_disk("Receipes/AllReceipes.json")
        source = self.vector_store.get_last_selected_source()
        filtered_receipes = self.filter_documents_by_source(all_receipes, source)
        # --> abspeichern zum Testen

        prompt = PromptTemplate.from_template(self.loader.read_from_file("RawIngredientExtraction.txt"))
        rawIngredientExtracor = RunnableRawIngredientExtracor(RawIngredientList, self.model, prompt)

        state['input'] = filtered_receipes
        raw_ingredients = rawIngredientExtracor.invoke(state)
        # --> abspeichern zum Testen
        
        # extract Complex Ingredients with Receipe Names from every receipe -> llm
        prompt = PromptTemplate.from_template(self.loader.read_from_file("IngredientConversion.txt"))
        complexIngredientExtracor = RunnableComplexIngredientExtractor(ComplexIngredientList, self.model, prompt)
        state['input'] = raw_ingredients
        complexIngredients = complexIngredientExtracor.invoke(state)
        


        # Result is a list of all ingredients with the corresponding receipe name
        

        # multiply all ingredients
        # bundle all ingredients and add to list -> list: external, mapping: llm
        
        
        return '\n'.join(f"{item}: {count}" for item, count in mealcount.items())
          
    
    def filter_documents_by_source(self, documents:List[Document], filterstr:str)->List[Document]:
        """
        Filters a list of documents to include only those where 'source' in metadata contains the specified filter string.
    
        Parameters:
            documents (list of Document): The list of Document objects to filter.
            filterstr (str): The substring to search for within each document's 'source' metadata.

        Returns:
            list of Document: A list of documents with 'source' metadata containing the specified substring.
        """
        filtered_docs = [
            doc for doc in documents
            if filterstr in doc.metadata.get('source', '')
        ]
        return filtered_docs
