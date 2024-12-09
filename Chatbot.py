
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
from FileLoader import FileLoader
from BaseModels import ComplexIngredientList
from Utils import load_documents_from_disk, store_complex_ingredient_list_on_disk
from Logger import Logger


class ChatbotWithHistory:
    def __init__(self, model, vector_store: VectorStore):
        self.model = model
        self.vector_store = vector_store
        self.loader = FileLoader()
        self.logger = Logger()
           
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
        df_restored = pd.read_json(StringIO(json_data), orient="split")
        
        # get list of receipe names from vector store
        recipes_and_ingredients = self.vector_store.get_recipes_from_last_source()

        # List_of_mapped_recipes = mapping_function(state['pd dataframe'], Ingredient_List) -> llm
        prompt = PromptTemplate.from_template(self.loader.read_from_file("ReceipeNameMapping.txt"))
        recipeMapper = RunnableRecipeMapper(self.model, prompt)
        
        state={}
        state['short_recipe_names'] = df_restored
        state['recipe_names_with_ingredients'] = recipes_and_ingredients 
        meals_by_mealtime = recipeMapper.invoke(state)
                                               
        # Load complexIngredients from disk
        source = self.vector_store.get_last_selected_source().split("\\")[-1]
        complex_ingredient_documents = load_documents_from_disk("Recipes/Json/ComplexIngredients.json")
        
        # Filter complexIngredients by source
        filtered_complex_ingredient_documents = self.filter_documents_by_source(complex_ingredient_documents, source)
        filtered_complex_ingredients_json = [json.loads(data.page_content) for data in filtered_complex_ingredient_documents]                
        complex_ingredients = [ComplexIngredientList(**item) for item in filtered_complex_ingredients_json]
        
        # [morgens, mittags, abends, nachmittags]
        mealtimes = df_restored.columns.tolist()
        mealtimes.remove('Tag')

        filtered_complexIngredients = []
        for mealtime in mealtimes:
            meals = meals_by_mealtime[mealtime] # morgens -> Counter
            for item in complex_ingredients:
                if item.recipe_name in meals.keys():
                    filtered_complexIngredients.append(item)
                       
        
        multiplier = RunnableMultiplier()
        state['input'] = filtered_complexIngredients
        state['count'] = meals_by_mealtime
        multiplied = multiplier.invoke(state)
        
        state['input'] = multiplied
        shopping_list_builder = RunnableShoppingListBuilder()
        shoppingList_categoryItems = shopping_list_builder.invoke(state)

        store_complex_ingredient_list_on_disk(complex_ingredients, 'logs/Chatbottest_original.json')
        store_complex_ingredient_list_on_disk(multiplied, 'logs/Chatbottest_multiplied.json')
        store_complex_ingredient_list_on_disk(shoppingList_categoryItems, 'logs/Chatbottest_shoppinglist.json')
             

        countedMeals = '\n'.join(
            f"{item}: {count}" 
            for mealcount in meals_by_mealtime.values()
            for item, count in mealcount.items()) 
        
        returnstring = ""
        for item in shoppingList_categoryItems:
            returnstring += f"{item.recipe_name}\n" # <--category
            for ingredient in item.ingredients:
                if(ingredient.unit != None):
                    returnstring += f" * {ingredient.name} {ingredient.quantity} x {ingredient.unit} ({ingredient.weight}g)\n"
                else:
                    returnstring += f" * {ingredient.name} {ingredient.weight}g\n"
        
        return "\n".join([countedMeals, "\n\nEinkaufsliste\n", returnstring])
          
    
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

    def LogMessage(self, message:str):
        self.logger.LogMessage(message, self)
        
    def LogException(self, exception:Exception, message:str = "Processing failed"):
        self.logger.LogException(exception, message, self)