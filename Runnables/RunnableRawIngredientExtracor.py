from langchain_core.runnables import Runnable
from langchain_core.runnables.passthrough import RunnableAssign
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain.docstore.document import Document
import json

from Runnables import RunnableDebugger as Debugger
from BaseModels import RawIngredientList
from Utils import FileLoader
from Utils import Logger

class RunnableRawIngredientExtracor(Runnable):
    def __init__(self, llm):
        self.llm = llm
        fileloader = FileLoader()
        self.extraction_prompt = PromptTemplate.from_template(fileloader.read_text_from_file("Recipes/Prompts/RawIngredientExtraction_prompt.txt"))
        self.output_validator_parser = PydanticOutputParser(pydantic_object=RawIngredientList)
        self.format_instruction_inserter = RunnableAssign({'format_instructions': lambda x: self.output_validator_parser.get_format_instructions()})   
        self.debugger = Debugger()
        self.logger = Logger()
           
    def invoke(self, state: dict, config=None)->Document:
        """expected dict: state['input'] = Document"""
                                
        self.LogMessage(f"Extracting raw ingredients")                             
        try:
            rawingredients = self.extract_ingredients().invoke(state)
        except Exception as exc:
            self.LogException(exc, f"Error extracting raw ingredients")
            raise Exception(f"Failed to extract raw ingredients")
        document = Document(page_content=json.dumps(rawingredients.dict(), ensure_ascii=False), metadata=state['input'].metadata)                                                            
        return document

    def extract_ingredients(self)->Runnable:
        return (self.format_instruction_inserter | self.extraction_prompt | self.debugger.Runnable_PrintTokencout(module=self) | self.llm | self.clean_and_format_output | self.output_validator_parser)
        
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

    def LogMessage(self, message:str):
        self.logger.LogMessage(message, self)
        
    def LogException(self, exception:Exception, message:str = "Processing failed"):
        self.logger.LogException(exception, message, self)
            