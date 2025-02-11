from langchain_core.runnables import Runnable
from langchain_core.documents import Document
import json

from BaseModels import ComplexIngredientList
from Utils import Logger

class RunnableEmbeddingStringExtractor(Runnable):
    def __init__(self):
        self.logger = Logger()
    
    def invoke(self, state: dict)->list[Document]:
        """
        expected dict: 
        state['input'] = list[Document]                
        """
        self.LogMessage(f"Extracting embedding strings for {len(state['input'])} recipes")    
        embeddingstrings = []
        for document in state['input']:

            complexIngredientList = ComplexIngredientList(**json.loads(document.page_content))

            ingredients = [ingredient.name for ingredient in complexIngredientList.ingredients]
            ingredients_str = ", ".join(ingredients)        
        
            text_to_embed = f"{complexIngredientList.recipe_name} - Ingredients: {ingredients_str}"
            embeddingstrings.append(Document(page_content=text_to_embed, metadata=document.metadata))
        self.LogMessage(f"Extracted embedding strings")    
        return embeddingstrings
    
    def LogMessage(self, message:str):
        self.logger.LogMessage(message, self)