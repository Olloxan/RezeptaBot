from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser 
from Logger import Logger
from Runnables import RunnableDebugger as Debugger

class RunnableRecipeMapper(Runnable):
    def __init__(self, llm, extraction_prompt):
        self.llm = llm
        self.prompt = extraction_prompt
        self.outputparser = StrOutputParser()      
        self.logger = Logger()
        self.debugger = Debugger()
    
    def invoke(self, state: dict)->list[str]:
        """ state['short_recipe_names'] = pd.DataFrame
            state['recipe_names_with_ingredients'] = full_recipe_names (with ingredients)
        """
        recipe_names = self.recipe_name_splitter(state)        
        mealtimes = self.get_meal_times(state)
        meals = []
        for mealtime in mealtimes:            
            short_recipe_names_by_mealtime = self.get_short_recipe_names_by_mealtime(state, mealtime)            
            try:
                for i in range(5):
                    self.logger.LogMessage(f"running loop with {mealtime} for the {i}th time")
                                
                    chain_output = self.runchain().invoke({"short_recipe_names" : short_recipe_names_by_mealtime['str'], "recipe_names" : recipe_names['str']})
                
                    chain_output_list = self.clean_string_and_convert_to_list(chain_output)
                    if self.output_conditions_are_met(chain_output_list, short_recipe_names_by_mealtime['list'], recipe_names['list']):                
                        break
                    if i == 4:
                        raise Exception("Recipe Mapping faild. Retry...")
                        meals = []
                meals.extend(chain_output_list)
            except Exception as exc:
                self.logger.LogMessage(exc)
        return meals
                        
    def recipe_name_splitter(self, state:dict)->dict: 
        """Converts: Schoko-Smoothie mit Beeren - Ingredients: B -> Schoko-Smoothie mit Beeren"""
        full_name_list:list[str] = [name.split(" - Ingredients")[0].strip() for name in state['recipe_names_with_ingredients']]
        full_receipe_names = "; ".join(full_name_list)
        return {'str' : full_receipe_names, 'list' : full_name_list}
    
    def get_meal_times(self, state:dict)->list[str]:
        mealtimes = state['short_recipe_names'].columns.tolist()
        mealtimes.remove('Tag')
        return mealtimes

    def get_short_recipe_names_by_mealtime(self, state:dict, mealtime:list[str])->dict:
        short_recipe_names = [item for item in state['short_recipe_names'][mealtime] if item != ""]
        short_recipe_name_string = "; ".join(short_recipe_names)
        return {'str' : short_recipe_name_string, 'list' : short_recipe_names}
    
    def runchain(self)->Runnable:
        return ( self.prompt | self.debugger.Runnable_PrintTokencout() | self.llm | self.outputparser)
    
    def clean_string_and_convert_to_list(self, string:str)->list[str]:                 
        string = (string
                .replace("\n", "")
                .replace(".", "")
                )
        output_list = [item.strip() for item in string.split(";")]
        return output_list
    
    def output_conditions_are_met(self, chain_output_list:list[str], short_name_list:list[str], full_name_list:list[str])->bool:
        """Output conditions: 
            1. is the output list a subset of the full name list
            2. have the output list and the list of short names the same length            
        """
        # prettyPrint("chain_output_list", chain_output_list)
        # prettyPrint("short_name_list", short_name_list)
        # prettyPrint("full_name_list", full_name_list)
        conditions:list[bool] = []
        conditions.append(set(chain_output_list).issubset(set(full_name_list)))
        
        # self.logger.LogMessage(f"missing elements: {set(chain_output_list) - set(full_name_list)}")
        # debuglen1 = len(chain_output_list)
        # debuglen2 = len(short_name_list)
        # self.logger.LogMessage(f"chain_output_list: {len(chain_output_list)}")
        # self.logger.LogMessage(f"short_name_list: {len(short_name_list)}")
        conditions.append(len(chain_output_list) == len(short_name_list))                            
        return all(conditions)
        # return True
