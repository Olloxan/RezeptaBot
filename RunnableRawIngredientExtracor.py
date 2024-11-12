from langchain_core.runnables import Runnable
import re
from langchain.output_parsers import PydanticOutputParser

class RunnableRawIngredientExtracor(Runnable):
    def __init__(self, schema_class, llm, extraction_prompt):
        self.llm = llm
        self.extraction_prompt = extraction_prompt
        self.output_validator_parser = PydanticOutputParser(pydantic_object=schema_class)
           
    def invoke(self, state: dict)->str:
        """expected dict: state['input'] = document"""
        # Step 1: Perform Extraction with LLM        
        unparsed_rawingredients = self.extract_ingredients(state['input'])
        
        # Step 2: Parsing the extracted information
        parsed_data = self.parse_extracted_ingredients(unparsed_rawingredients)        
        return parsed_data

    def extract_ingredients(self, input):
        return (self.extraction_prompt | self.llm).invoke(input)
    
    def parse_extracted_ingredients(self, extracted_text):
        # split if multiple ingrdients objects
        result = re.sub(r'}\s*{', '}\n{', extracted_text)            
        json_objects = result.split('}\n{')                    
        
        separated_objects = []        
        for json_obj in json_objects:        
            cleaned_json = self.clean_and_format_output(json_obj)           
            raw_ingredient = self.output_validator_parser.invoke(cleaned_json)                    
            separated_objects.append(raw_ingredient)                
        return separated_objects       

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
