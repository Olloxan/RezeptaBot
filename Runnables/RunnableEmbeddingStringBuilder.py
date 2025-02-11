from langchain_core.runnables import Runnable
from langchain_core.runnables.passthrough import RunnableAssign
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document


from Runnables import RunnableDebugger as Debugger
from Utils import Logger
from BaseModels import RawIngredientList
from Utils import FileLoader

class RunnableEmbeddingStringBuilder(Runnable):
    def __init__(self, llm):
        self.llm = llm
        fileloader = FileLoader()
        self.extraction_prompt = PromptTemplate.from_template(fileloader.read_text_from_file("Recipes/Prompts/EmbeddingStringExtraction_prompt.prompt"))
        self.output_validator_parser = PydanticOutputParser(pydantic_object=RawIngredientList)
        self.format_instruction_inserter = RunnableAssign({'format_instructions': lambda x: self.output_validator_parser.get_format_instructions()})   
        self.debugger = Debugger()
        self.logger = Logger()
           
    def invoke(self, state: dict)->list[Document]:
        """expected dict: state['input'] = List[document] -> Complete Recipe"""
        
        ingredient_list = []
        for i, document in enumerate(state['input']):    
            try:
                self.LogMessage(f"Extracting raw ingredients: document {i} of {len(state['input'])-1}")     
                        
                embeddingtext = self.extract_ingredients().invoke({'input': document})
                
                doc = Document(page_content=embeddingtext, metadata=document.metadata)                
                ingredient_list.append(doc)
                
            except Exception as exc:
                self.LogException(exc, f"Error processing document {i}. Recipe is: {document.page_content}. Source is: {document.metadata['source']}")
        return ingredient_list

    def extract_ingredients(self)->Runnable:
        return (self.format_instruction_inserter | self.extraction_prompt | self.debugger.Runnable_PrintTokencout(module=self) | self.llm | self.clean_and_format_output | self.output_validator_parser | self.generate_embedding_text)
        
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

    def generate_embedding_text(self, recipe: RawIngredientList) -> str:
        # Join the ingredients into a single string
        ingredients_str = ", ".join(recipe.ingredients)        
        # Create the embedding string
        text_to_embed = f"{recipe.recipe_name} - Ingredients: {ingredients_str}"
    
        return text_to_embed
    
    def LogMessage(self, message:str):
        self.logger.LogMessage(message, self)
        
    def LogException(self, exception:Exception, message:str = "Processing failed"):
        self.logger.LogException(exception, message, self)