from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser 
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import DocArrayInMemorySearch
from typing import Counter
from Utils import Logger
from Runnables import RunnableDebugger as Debugger
from Utils import FileLoader

class RunnableRecipeMapper(Runnable):
    def __init__(self, llm):
        self.llm = llm
        
        self.outputparser = StrOutputParser()      
        self.logger = Logger()
        self.debugger = Debugger()
        self.num_tries = 1
    
    def invoke(self, state: dict)->dict[str, Counter]:
        """ state['short_recipe_names'] = pd.DataFrame
            state['recipe_names_with_ingredients'] = full_recipe_names (with ingredients)
        """
        recipe_names = self.extract_recipe_names_from_embeddingstrings(state)        
        self.LogMessage(f"recipe_names: {recipe_names['str']}")
        mealtimes = self.extract_mealtimes(state)
        meals = {}
        
        embeddings = OllamaEmbeddings(model="mxbai-embed-large") 
        self.LogMessage("Start Embedding")
        docarrayinmemory = DocArrayInMemorySearch.from_texts(recipe_names['list'], embedding=embeddings)
        self.LogMessage("Embedding finished")

        retriever = docarrayinmemory.as_retriever(search_kwargs={"k": 1})
        
        for mealtime in mealtimes:            
            short_recipe_names_by_mealtime = self.extract_short_recipe_names_by_mealtime(state, mealtime)                        
                                                       
            extracted_recipes = []
            cache = {}
            for item in short_recipe_names_by_mealtime['list']:
                self.LogMessage(f"retriving: {item}")
                
                if item in cache.keys():                                
                    retrival = cache[item]
                    self.LogMessage(f"From cache: {retrival[0].page_content}")    
                else:                    
                    retrival = retriever.invoke(item)
                    cache[item] = retrival
                    self.LogMessage(f"From Retriver: {retrival[0].page_content}")                
                extracted_recipes.append(retrival[0].page_content)
               
            meals[mealtime] = Counter(extracted_recipes)                       
        return meals
                        
    def extract_recipe_names_from_embeddingstrings(self, state:dict)->dict: 
        """ 
        Extract recipe names form embedding strings
        e.g. Schoko-Smoothie mit Beeren - Ingredients: B -> Schoko-Smoothie mit Beeren

        :return: A dictionary with keys 'str' (semicolon-joined recipes) and 'list' (list of recipes).
        """
        full_name_list:list[str] = [name.split(" - Ingredients")[0].strip() for name in state['recipe_names_with_ingredients']]
        full_receipe_names = "; ".join(full_name_list)
        return {'str' : full_receipe_names, 'list' : full_name_list}
    
    def extract_mealtimes(self, state:dict)->list[str]:
        """
        Retrieve a list of meal-time columns names (['Morgens', 'Mittags', 'Nachmittags', 'Abends'])
        from the 'short_recipe_names' DataFrame within the given state dictionary.
        """
        mealtimes = state['short_recipe_names'].columns.tolist()
        mealtimes.remove('Tag')
        return mealtimes

    def extract_short_recipe_names_by_mealtime(self, state:dict, mealtime:str)->dict:
        """
        Retrieve all non-empty recipe names for a given mealtime from the 'short_recipe_names'
        DataFrame in the provided state dictionary. The function returns a dictionary containing:
        1) 'list': A list of recipe names
        2) 'str' : A semicolon-separated string of the same recipe names

        :param state: A dictionary with a pandas DataFrame under 'short_recipe_names' (with columns for different meal times).
        :param mealtime: The name of the column (e.g., 'Morgens', 'Mittags') from which the recipes should be extracted.
        :return: A dictionary with keys 'str' (semicolon-joined recipes) and 'list' (list of recipes).
        """
        short_recipe_names = [item for item in state['short_recipe_names'][mealtime] if item != ""]
        short_recipe_name_string = "; ".join(short_recipe_names)
        return {'str' : short_recipe_name_string, 'list' : short_recipe_names}
    
    def runchain(self)->Runnable:
        return ( self.prompt 
                | self.debugger.Runnable_PrintTokencout(module=self) 
                | self.llm 
                | self.debugger.Runnable_PrintTextWithLabel(label="LLM output: ", module=self) 
                | self.outputparser)
    
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
        conditions:list[bool] = []
        
        is_subset = set(chain_output_list).issubset(set(full_name_list))        
        if not is_subset:
            self.LogMessage(f"missing elements: {set(chain_output_list) - set(full_name_list)}")
            
        conditions.append(is_subset)
               
        is_same_length = len(chain_output_list) == len(short_name_list)
        if not is_same_length:
            self.LogMessage(f"chain_output_list: {len(chain_output_list)}")
            self.LogMessage(f"short_name_list: {len(short_name_list)}")

        conditions.append(len(chain_output_list) == len(short_name_list))                            
        return all(conditions)
        
    def LogMessage(self, message:str):
        self.logger.LogMessage(message, self)
            