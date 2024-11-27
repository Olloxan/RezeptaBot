
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
        state['count'] = Counter
        """
        
        counter = state['count']
        counterItems = counter.keys()
        
        complexIngredientLists = [copy.deepcopy(ingredientlist) for ingredientlist in state['input'] if ingredientlist.recipe_name in counterItems]

        for complexIngredientList in complexIngredientLists:
            count = counter[complexIngredientList.recipe_name]
            for ingredient in complexIngredientList.ingredients:
                ingredient.quantity = ingredient.quantity * count if ingredient.quantity is not None else 0
                ingredient.weight = ingredient.weight * count if ingredient.weight is not None else 0

        return complexIngredientLists
