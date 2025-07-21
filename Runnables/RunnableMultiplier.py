
from langchain_core.runnables import Runnable
import copy

from BaseModels import ComplexIngredientList
from Utils import Logger

class RunnableMultiplier(Runnable):
    def __init__(self):
        self.logger = Logger()
        

    def invoke(self, state: dict)->list[ComplexIngredientList]:
        """
        expected dict: 
        state['input'] = List[ComplexIngredientList]
        state['count'] = dict[str,Counter]
        """
        
        counter_dict = state['count']                
        complexIngredientLists = []
        for key in counter_dict:
            
            complexIngredientList_by_mealtime = [copy.deepcopy(ingredientlist) for ingredientlist in state['input'] if ingredientlist.recipe_name in counter_dict[key]]
        
            for complexIngredientList in complexIngredientList_by_mealtime:
                multiplier = counter_dict[key][complexIngredientList.recipe_name]
                if key in ['Morgens','Mittags']: multiplier #*= 1.5
                if key in ['Nachmittags']: multiplier #*= 2
                self.LogMessage(f"Processing meals for: {key}")
                
                for ingredient in complexIngredientList.ingredients:
                    self.LogMessage(f"Multiplying {ingredient.name} by {multiplier}")
                    ingredient.quantity = ingredient.quantity * multiplier if ingredient.quantity is not None else 0
                    ingredient.weight = ingredient.weight * multiplier if ingredient.weight is not None else 0
                complexIngredientLists.append(complexIngredientList)
        return complexIngredientLists
    
    def LogMessage(self, message:str):
        self.logger.LogMessage(message, self)
