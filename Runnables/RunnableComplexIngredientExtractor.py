from langchain_core.runnables import Runnable
from langchain_core.runnables.passthrough import RunnableAssign
from Runnables import RunnableDebugger as Debugger
from langchain.output_parsers import PydanticOutputParser
from Logger import Logger

class RunnableComplexIngredientExtractor(Runnable):
    def __init__(self, schema_class, llm, extraction_prompt):
        self.llm = llm
        self.extraction_prompt = extraction_prompt
        self.output_validator_parser = PydanticOutputParser(pydantic_object=schema_class)
        self.format_instruction_inserter = RunnableAssign({'format_instructions' : lambda x: self.output_validator_parser.get_format_instructions()})   
        self.debugger = Debugger()
        self.logger = Logger()

    def invoke(self, state:dict):
        """ expected dict: state['input'] = List[RawIngredientList] """
        complex_ingredient_list = []        
        for i, rawIngredientList in enumerate(state['input']):    
            success = True
            for i in range(5): # try multiple times to extract the data
                try:
                    self.logger.LogMessage(f"Attempting Complex Ingredient Extraction for the {i}th time")
                    success = True
                    # Step 1: Perform Extraction with LLM                   
                    if rawIngredientList.recipe_name =='':
                        continue            
                    unparsed_rawingredients = self.extract_complex_ingredients().invoke({'input' : rawIngredientList})
                    # Step 2: Parsing the extracted information
                    parsed_data = self.parse_extracted_ingredients(unparsed_rawingredients)                      
                    break
                except Exception as exc:
                    self.logger.LogException(exc, f"Error decoding JSON")
                    success = False
            if not success:
                raise Exception("Failed to extract data")        
        complex_ingredient_list.append(parsed_data)
        return complex_ingredient_list

    def extract_complex_ingredients(self)->Runnable:
        return (self.format_instruction_inserter | self.extraction_prompt | self.debugger.Runnable_PrintTokencout() | self.llm )
    

    def parse_extracted_ingredients(self, extracted_text):
        # split if multiple ingrdients objects
        cleaned_output_string = self.clean_and_format_output(extracted_text)
        complex_ingredient_list = self.output_validator_parser.invoke(cleaned_output_string)                    
                            
        return complex_ingredient_list       

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
