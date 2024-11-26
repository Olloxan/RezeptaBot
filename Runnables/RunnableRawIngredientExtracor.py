from langchain_core.runnables import Runnable
from langchain_core.runnables.passthrough import RunnableAssign
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from Runnables import RunnableDebugger as Debugger
from Logger import Logger
from BaseModels import RawIngredientList
from Utils import read_from_file

class RunnableRawIngredientExtracor(Runnable):
    def __init__(self, llm):
        self.llm = llm
        self.extraction_prompt = PromptTemplate.from_template(read_from_file("Recipes/Prompts/RawIngredientExtraction_prompt.txt"))
        self.output_validator_parser = PydanticOutputParser(pydantic_object=RawIngredientList)
        self.format_instruction_inserter = RunnableAssign({'format_instructions': lambda x: self.output_validator_parser.get_format_instructions()})   
        self.debugger = Debugger()
        self.logger = Logger()
           
    def invoke(self, state: dict)->list[RawIngredientList]:
        """expected dict: state['input'] = List[document]"""
        
        ingredient_list = []
        for i, page in enumerate(state['input']):    
            try:
                self.logger.LogMessage(f"Extracting raw ingredients: document {i} from {len(state['input'])-1}")     
                        
                rawingredients = self.extract_ingredients().invoke({'input': page})
                           
                ingredient_list.append(rawingredients)
            except Exception as exc:
                self.logger.LogException(exc, f"Error processing document {i}. Recipe is: {page.page_content}. Source is: {page.metadata['source']}")
        return ingredient_list

    def extract_ingredients(self)->Runnable:
        return (self.format_instruction_inserter | self.extraction_prompt | self.debugger.Runnable_PrintTokencout() | self.llm | self.clean_and_format_output | self.output_validator_parser)
        
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
