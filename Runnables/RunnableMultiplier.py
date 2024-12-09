
from langchain_core.runnables import Runnable
import copy

from BaseModels import ComplexIngredientList

class RunnableMultiplier(Runnable):
    def __init__(self):
        pass

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
                count = counter_dict[key][complexIngredientList.recipe_name]
                if key in ['Morgens', 'Nachmittags']: count *= 1.5
                for ingredient in complexIngredientList.ingredients:
                    ingredient.quantity = ingredient.quantity * count if ingredient.quantity is not None else 0
                    ingredient.weight = ingredient.weight * count if ingredient.weight is not None else 0
                complexIngredientLists.append(complexIngredientList)
        return complexIngredientLists
