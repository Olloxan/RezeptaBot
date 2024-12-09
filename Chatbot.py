
from venv import logger
from langchain_core.output_parsers import StrOutputParser 
from operator import itemgetter
from langchain_core.prompts import PromptTemplate
from typing import Counter, List, Union, Dict
from langchain_core.runnables import RunnableBranch
from langchain.docstore.document import Document
import pandas as pd
from io import StringIO
import json

from Runnables import RunnableRecipeMapper, RunnableMultiplier, RunnableShoppingListBuilder
from VectorStore import VectorStore

from BaseModels import ComplexIngredientList
from Utils import FileLoader
from Logger import Logger


class ChatbotWithHistory:
    def __init__(self, model, vector_store: VectorStore):
        self.model = model
        self.vector_store = vector_store        
        self.logger = Logger()
        self.fileLoader = FileLoader()
           
    def preloadModel(self):
        self.logger.LogMessage("Preloading chatbot model")
        self.model.invoke("")
        self.logger.LogMessage("Model loaded")
                                  
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
            Dein Name ist Susi Sonnenschein und liebst Pfannkuchen und Gänseblümchen.         
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
    
    def build_history(self, history: list[list[Union[None, str]]]) -> str:              
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
        data_frame_weekplan = pd.read_json(StringIO(json_data), orient="split")
        
        # get list of receipe names from vector store
        recipes_and_ingredients = self.vector_store.get_recipes_from_last_source()

        # Recipe Mapping
        
        recipeMapper = RunnableRecipeMapper(self.model)
        
        state={}
        state['short_recipe_names'] = data_frame_weekplan
        state['recipe_names_with_ingredients'] = recipes_and_ingredients 
        
        try:
            meals_by_time_of_day = recipeMapper.invoke(state)
        except Exception as exc:
            self.LogException(exc)
            return "Fehler beim Rezept Matching. Versuche es erneut"
        
        # Recipe filtering
        source = self.vector_store.get_last_selected_source().split("\\")[-1]
        complex_ingredient_documents = self.fileLoader.load_documents_from_disk("Recipes/Json/ComplexIngredients.json")
                
        all_complex_ingredients_of_the_week = self.filter_ComplexIngredienta_by_source(complex_ingredient_documents, source)                        
        filtered_complexIngredients = self.filter_complexIngredients_by_weekplan(all_complex_ingredients_of_the_week, meals_by_time_of_day)        
                       
        # recipe multiplying
        multiplier = RunnableMultiplier()
        state['input'] = filtered_complexIngredients
        state['count'] = meals_by_time_of_day
        multiplied = multiplier.invoke(state)
        
        # shopping list building
        state['input'] = multiplied
        shopping_list_builder = RunnableShoppingListBuilder()
        shoppingList_categoryItems = shopping_list_builder.invoke(state)
       
        self.fileLoader.store_complex_ingredient_list_on_disk(shoppingList_categoryItems, 'logs/Chatbottest_shoppinglist.json')
            
        combined_meal_counter = sum(meals_by_time_of_day.values(), Counter())
        # return string building
        countedMeals = '\n'.join(f"{item}: {count}" for item, count in combined_meal_counter.items()) 
        
        returnstring = ""
        for recipe in shoppingList_categoryItems:
            returnstring += f"{recipe.recipe_name}\n" # <--category
            for ingredient in recipe.ingredients:
                if(ingredient.unit != None):
                    returnstring += f" * {ingredient.name} {ingredient.quantity} x {ingredient.unit} ({ingredient.weight}g)\n"
                else:
                    returnstring += f" * {ingredient.name} {ingredient.weight}g\n"
        
        return "\n".join([countedMeals, "\n\nEinkaufsliste\n", returnstring])
          
    
    def filter_ComplexIngredienta_by_source(self, documents:List[Document], filterstr:str)->list[ComplexIngredientList]:
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
        filtered_complex_ingredients_json = [json.loads(data.page_content) for data in filtered_docs]                
        complex_ingredients = [ComplexIngredientList(**item) for item in filtered_complex_ingredients_json]
        return complex_ingredients

    def filter_complexIngredients_by_weekplan(self, complexIngredients:list[ComplexIngredientList], meals_by_time_of_day:dict[str, Counter] )->list[ComplexIngredientList]:
        filtered_complexIngredients = []
        for recipes_counter in meals_by_time_of_day.values():             
            for recipe in complexIngredients:
                if recipe.recipe_name in recipes_counter.keys():
                    filtered_complexIngredients.append(recipe)
        return filtered_complexIngredients        

    def LogMessage(self, message:str):
        self.logger.LogMessage(message, self)
        
    def LogException(self, exception:Exception, message:str = "Processing failed"):
        self.logger.LogException(exception, message, self)