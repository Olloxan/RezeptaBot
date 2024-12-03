from langchain_core.runnables import Runnable

from BaseModels import ComplexIngredientList, Ingredient


class RunnableShoppingListBuilder(Runnable):
    def __init__(self):        
        self.shopping_list = []
        self.categories = {"Obst/Gemüse":[], "Vegan":[], "Milchprodukte":[], "Tiefkühl":[], "Sonstiges":[]}
        
    def invoke(self, state:dict) ->list[ComplexIngredientList]:
        """ expected dict: state['input'] = List[ComplexIngredientList] 
            The idea is to recycle a complexIngredientList Object to sort the ingredients by Category where ReciperName is the categorys
        """
        recipe_ingredient_list = state['input']
        
        for recipe in recipe_ingredient_list:          
            ingredients = self.retrieveIngredients(recipe)                       
            self.addRecipesToCategories(ingredients)
        
            
        # optionaler vorverarbeitungsschritt, Zutaten zusammen fassen

        self.createShoppingList()
        return self.shopping_list
    
    # def fooRunnable(self)->Runnable:
    #     """ select one of the following categories for the ingredent: Obst/Gemüse, Vegan, Milchprodukte, Tiefkühl, Sonstiges """
    #     return (prompt | model | strOutputParser)

    def retrieveIngredients(self, complexIngredientsList:ComplexIngredientList)->list[Ingredient]:
        return complexIngredientsList.ingredients
    
    def addRecipesToCategories(self, ingredients:list[Ingredient]):
        for ingredient in ingredients:
            self.categories[ingredient.category].append(ingredient)

    def createShoppingList(self):
        for category in self.categories:                    
            ingredients:list[Ingredient] = self.categories[category]            
            destictIngredientList = ComplexIngredientList(recipe_name=category) 
            for ingredient in ingredients:
                # to lower 
                if ingredient.name.lower() not in [x.name.lower() for x in destictIngredientList.ingredients]:
                    destictIngredientList.ingredients.append(ingredient)
                else:
                    temp_ingredient = [x for x in destictIngredientList.ingredients if x.name.lower() == ingredient.name.lower()][0]
                    temp_ingredient.quantity += ingredient.quantity
                    temp_ingredient.weight += ingredient.weight                                               
            self.shopping_list.append(destictIngredientList)
