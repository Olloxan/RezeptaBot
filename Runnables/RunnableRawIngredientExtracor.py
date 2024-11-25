from langchain_core.runnables import Runnable
from langchain_core.runnables.passthrough import RunnableAssign
import re
from langchain.output_parsers import PydanticOutputParser
from Runnables import RunnableDebugger as Debugger
from BaseModels import RawIngredientList

class RunnableRawIngredientExtracor(Runnable):
    def __init__(self, schema_class, llm, extraction_prompt):
        self.llm = llm
        self.extraction_prompt = extraction_prompt
        self.output_validator_parser = PydanticOutputParser(pydantic_object=schema_class)
        self.format_instruction_inserter = RunnableAssign({'format_instructions' : lambda x: self.output_validator_parser.get_format_instructions()})   
        self.debugger = Debugger()
           
    def invoke(self, state: dict)->list[RawIngredientList]:
        """expected dict: state['input'] = List[document]"""
        
        ingredient_list = []
        for i, page in enumerate(state['input']):    
         
            # Step 1: Perform Extraction with LLM        
            unparsed_rawingredients = self.extract_ingredients().invoke({'input': page})
        
            # Step 2: Parsing the extracted information
            parsed_data = self.parse_extracted_ingredients(unparsed_rawingredients)        
            ingredient_list.extend(parsed_data)
        return ingredient_list

    def extract_ingredients(self)->Runnable:
        return (self.format_instruction_inserter | self.extraction_prompt | self.debugger.Runnable_PrintTokencout() | self.llm | self.debugger.Runnable_PrintStructureWithLabel(label="Raw Extraction"))
    
    def parse_extracted_ingredients(self, extracted_text:str)->list[RawIngredientList]:
        # split if multiple ingrdients objects
        result = re.sub(r'}\s*{', '}\n{', extracted_text)            
        json_objects = result.split('}\n{')                    
        
        separated_objects = []        
        for json_obj in json_objects:        
            cleaned_json = self.clean_and_format_output(json_obj)           
            raw_ingredient = self.output_validator_parser.invoke(cleaned_json)                    
            separated_objects.append(raw_ingredient)                
        return separated_objects       

    def clean_and_format_output(self, string:str)->str:
        if '{' not in string: string = '{' + string
        if '}' not in string: string = string + '}'
        string = (string
            .replace("\\_", "_")
            .replace("\n", " ")
            .replace("\]", "]")
            .replace("\[", "[")
        ) 
        return string 
