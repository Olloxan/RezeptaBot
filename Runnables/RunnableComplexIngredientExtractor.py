from langchain_core.runnables import Runnable
from langchain_core.runnables.passthrough import RunnableAssign
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
from langchain.docstore.document import Document
import json

from langsmith.utils import is_version_greater_or_equal

from Runnables import RunnableDebugger as Debugger
from langchain_core.prompts import PromptTemplate
from Logger import Logger
from Utils import read_text_from_file
from BaseModels import ComplexIngredientList, RawIngredientList, Ingredient

class RunnableComplexIngredientExtractor(Runnable):
    def __init__(self, llm):
        self.llm = llm
        self.extraction_prompt = PromptTemplate.from_template(read_text_from_file("Recipes/Prompts/ComplexIngredientExtraction_prompt.txt"))
        self.category_prompt = PromptTemplate.from_template(read_text_from_file("Recipes/Prompts/ComplexIngredientCategory_prompt.txt"))
        self.output_validator_parser = PydanticOutputParser(pydantic_object=ComplexIngredientList)
        self.format_instruction_inserter = RunnableAssign({'format_instructions' : lambda x: self.output_validator_parser.get_format_instructions()})   
        self.debugger = Debugger()
        self.logger = Logger()
        self.num_extraction_tries = 2
        self.ingredient_list:list[Ingredient] = []
        self.strOutputParser = StrOutputParser()

    def invoke(self, state:dict)->Document:
        """ expected dict: state['input'] = Document """
                            
        rawIngredientList = RawIngredientList(**json.loads(state['input'].page_content))
        self.LogMessage(f"Extracting Complex Ingredients for: {rawIngredientList.recipe_name}")
        success = True
        for i in range(self.num_extraction_tries): # try multiple times to extract the data
            try:
                self.LogMessage(f"Try: {i}")
                success = True                                                         
                complex_ingredients = (self.extract_complex_ingredients() | self.set_category).invoke({'input' : rawIngredientList}) 
                                       
                break
            except Exception as exc:
                self.LogException(exc, f"Error decoding JSON")
                success = False
        if not success:
            raise Exception(f"Failed to extract Complex Ingredients for {rawIngredientList.recipe_name} {self.num_extraction_tries} times")
                        
        document = Document(page_content=json.dumps(complex_ingredients.dict(), ensure_ascii=False), metadata=state['input'].metadata)         
        return document

    def extract_complex_ingredients(self)->Runnable:
        return (self.format_instruction_inserter 
                | self.extraction_prompt 
                | self.debugger.Runnable_PrintTokencout() 
                | self.llm
                | self.clean_and_format_output 
                | self.output_validator_parser 
                | self.set_quantity_none)
        
    def clean_and_format_output(self, string):
        if '{' not in string: string = '{' + string
        if '}' not in string: string = string + '}'
        string = (string
            .replace("\\_", "_")
            .replace("\n", " ")
            .replace("\]", "]")
            .replace("\[", "[")
        ) 
        return string 
    
    def set_quantity_none(self, complexIngredientList:ComplexIngredientList)->ComplexIngredientList:
        for ingredient in complexIngredientList.ingredients:
            if ingredient.unit == None:
                ingredient.quantity = None
        return complexIngredientList
        
    def set_category(self, complexIngredientList:ComplexIngredientList)->ComplexIngredientList:
        self.LogMessage(f"Setting ingredient categories for {complexIngredientList.recipe_name}")
        for ingredient in complexIngredientList.ingredients:
            # if Item already exists, no call to llm
            if not self.is_ingredient_on_list(ingredient):
                # llm call mit kathegorie als ausgang
                ingredient.category = self.select_category().invoke({'input' : ingredient.name})                
                self.LogMessage(f"Ingredient: {ingredient.name} -> {ingredient.category}")
                self.ingredient_list.append(ingredient)
            else:                
                ingredient.category = self.get_category(ingredient)
                self.LogMessage(f"Ingredient on the list: {ingredient.name} -> {ingredient.category}")

        return complexIngredientList
    
    def is_ingredient_on_list(self, ingredient):
        is_on_list = False
        for item in self.ingredient_list:
            if ingredient.name == item.name:
                ingredient.category = item.category            
                is_on_list = True
                break
        return is_on_list
    
    def select_category(self)->Runnable:
        """ select one of the following categories for the ingredent: Obst/Gemüse, Vegan, Milchprodukte, Tiefkühl, Sonstiges """
        return (self.category_prompt | self.debugger.Runnable_PrintTokencout() | self.llm | self.strOutputParser)
    
    def get_category(self, ingredient):
        for item in self.ingredient_list:
            if ingredient.name == item.name:
                return item.category
            
    def LogMessage(self, message:str):
        self.logger.LogMessage(message, self)
        
    def LogException(self, exception:Exception, message:str = "Processing failed"):
        self.logger.LogException(exception, message, self)