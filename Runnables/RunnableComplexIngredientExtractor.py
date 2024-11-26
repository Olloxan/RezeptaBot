from langchain_core.runnables import Runnable
from langchain_core.runnables.passthrough import RunnableAssign
from Runnables import RunnableDebugger as Debugger
from langchain.output_parsers import PydanticOutputParser

from langchain_core.prompts import PromptTemplate
from Logger import Logger
from Utils import read_from_file
from BaseModels import ComplexIngredientList

class RunnableComplexIngredientExtractor(Runnable):
    def __init__(self, llm):
        self.llm = llm
        self.extraction_prompt = PromptTemplate.from_template(read_from_file("Recipes/Prompts/ComplexIngredientExtraction_prompt.txt"))
        self.output_validator_parser = PydanticOutputParser(pydantic_object=ComplexIngredientList)
        self.format_instruction_inserter = RunnableAssign({'format_instructions' : lambda x: self.output_validator_parser.get_format_instructions()})   
        self.debugger = Debugger()
        self.logger = Logger()
        self.num_extraction_tries = 5

    def invoke(self, state:dict):
        """ expected dict: state['input'] = List[RawIngredientList] """
        
        complex_ingredient_list = []                
        for i, rawIngredientList in enumerate(state['input']):    
            self.logger.LogMessage(f"Extracting Complex Ingredients for: {rawIngredientList.recipe_name}. Recipe {i} from {len(state['input'])}")
            success = True
            for j in range(self.num_extraction_tries): # try multiple times to extract the data
                try:
                    self.logger.LogMessage(f"Try: {j}")
                    success = True
                                                         
                    parsed_data = self.extract_complex_ingredients().invoke({'input' : rawIngredientList})
                    
                    break
                except Exception as exc:
                    self.logger.LogException(exc, f"Error decoding JSON")
                    success = False
            if not success:
                self.logger.LogException(Exception("Failed to extract Complex Ingredients"), f"Processing failed 5 times. Continuing")
                continue
            complex_ingredient_list.append(parsed_data)
        return complex_ingredient_list

    def extract_complex_ingredients(self)->Runnable:
        return (self.format_instruction_inserter 
                | self.extraction_prompt 
                | self.debugger.Runnable_PrintTokencout() 
                | self.llm 
                | self.clean_and_format_output 
                | self.output_validator_parser 
                | self.set_quantity_null)
         
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
    
    def set_quantity_null(self, complexIngredientList:ComplexIngredientList)->ComplexIngredientList:
        for ingredient in complexIngredientList.ingredients:
            if ingredient.unit == None:
                ingredient.quantity = None
        return complexIngredientList
