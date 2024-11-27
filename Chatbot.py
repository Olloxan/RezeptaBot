
from langchain_core.output_parsers import StrOutputParser 
from operator import itemgetter
from langchain_core.prompts import PromptTemplate
from typing import Counter, List, Union, Dict
from langchain_core.runnables import RunnableLambda, RunnableAssign, RunnableBranch
from langchain.docstore.document import Document
import pandas as pd
import concurrent.futures
import threading
import json

from Runnables import RunnableComplexIngredientExtractor, RunnableRawIngredientExtracor, RunnableRecipeMapper, RunnableMultiplier
from VectorStore import VectorStore
from FileLoader import FileLoader
from BaseModels import RawIngredientList, ComplexIngredientList
from Utils import load_documents_from_disk, store_complex_ingredient_list_on_disk

from functools import partial
from rich.console import Console
from rich.style import Style
from rich.theme import Theme

console = Console()
base_style = Style(color="#76B900", bold=True)
pprint = partial(console.print, style=base_style)


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
            (lambda state: state['message'].startswith('retrieval:'), lambda state: self.allRecipesOfThisWeek(state)),
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
    def allRecipesOfThisWeek(self, state: Dict)->str:
        """retrieve a list of receipe names from the json file based on the metadata"""
        currentRecipeSelectionIndex = state['message'].split(":")[1]                        
        # retrieve a list of recipes with the same metadata
        recipeList, source = self.vector_store.get_receipe_List(currentRecipeSelectionIndex)
        
        joined_recipes = "\n\n".join(recipeList)
        joined_recipes += f"\n\nSource: {source}"
        return joined_recipes
    
    ################################ shoppinglist ################################
    def createShoppingList(self, state):
        """create a shopping list based on the selected recipes"""
        
        # restore pandas dataframe from json
        json_data = state['message'].split("shoppinglist:")[1]
        df_restored = pd.read_json(json_data, orient="split")
        
        # get list of receipe names from vector store
        recipes_and_ingredients = self.vector_store.get_recipes_from_last_source()

        # List_of_mapped_recipes = mapping_function(state['pd dataframe'], Ingredient_List) -> llm
        prompt = PromptTemplate.from_template(self.loader.read_from_file("ReceipeNameMapping.txt"))
        recipeMapper = RunnableRecipeMapper(self.model, prompt)
        
        state={}
        state['short_recipe_names'] = df_restored
        state['recipe_names_with_ingredients'] = recipes_and_ingredients 
        output = recipeMapper.invoke(state)
                        
        # count all recipes -> Dict with receipenames as Key and count as value
        mealcount = Counter(output)
        
        # Load complexIngredients from disk
        source = self.vector_store.get_last_selected_source().split("\\")[-1]
        complex_ingredient_documents = load_documents_from_disk("logs/ComplexIngredients.json")
        filtered_complex_ingredient_documents = self.filter_documents_by_source(complex_ingredient_documents, source)
        filtered_complex_ingredients_json = [json.loads(data.page_content) for data in filtered_complex_ingredient_documents]        
        complex_ingredients = [ComplexIngredientList(**item) for item in filtered_complex_ingredients_json]

        filtered_complexIngredients = [item for item in complex_ingredients if item.recipe_name in mealcount.keys()]
                       
        
        multiplier = RunnableMultiplier()
        state['input'] = filtered_complexIngredients
        state['count'] = mealcount
        multiplied = multiplier.invoke(state)
        
        store_complex_ingredient_list_on_disk(complex_ingredients, 'logs/Chatbottest_original.json')
        store_complex_ingredient_list_on_disk(multiplied, 'logs/Chatbottest_multiplied.json')
                
        # multiply all ingredients
        # bundle all ingredients and add to list -> list: external, mapping: llm
        
        countedMeals = '\n'.join(f"{item}: {count}" for item, count in mealcount.items())
                
        calculated = "\n\n".join(f"{recipe.recipe_name}:\n" + "\n".join(f"{ing.name}: {ing.quantity or ''} {ing.unit or ''} ({ing.weight} g)" for ing in recipe.ingredients) for recipe in multiplied)
        
        return "\n".join([countedMeals, "\nMultiplizierte Mengen\n", calculated])
          
    
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
