from langchain_core.runnables import Runnable
from langchain_core.runnables.passthrough import RunnableAssign
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
import json
import re


from Runnables import RunnableDebugger as Debugger
from langchain_core.prompts import PromptTemplate
from Utils import Logger
from Utils import FileLoader
from BaseModels import ComplexIngredientList, RawIngredientList, Ingredient

class RunnableComplexIngredientExtractor(Runnable):
    def __init__(self, llm):
        self.llm = llm
        fileloader = FileLoader()
        self.extraction_prompt = PromptTemplate.from_template(fileloader.read_text_from_file("Recipes/Prompts/ComplexIngredientExtraction_prompt.txt"))
        self.category_prompt = PromptTemplate.from_template(fileloader.read_text_from_file("Recipes/Prompts/ComplexIngredientCategory_prompt.txt"))
        self.output_validator_parser = PydanticOutputParser(pydantic_object=ComplexIngredientList)
        self.format_instruction_inserter = RunnableAssign({'format_instructions' : lambda x: self.output_validator_parser.get_format_instructions()})   
        self.debugger = Debugger()
        self.logger = Logger()
        self.num_extraction_tries = 2
        self.ingredient_list:list[Ingredient] = []
        self.strOutputParser = StrOutputParser()

    def invoke(self, state:dict, config=None)->Document:
        """ expected dict: state['input'] = Document """    
        
        success = True
        for i in range(self.num_extraction_tries): # try multiple times to extract the data
            try:
                self.LogMessage(f"Try: {i}")
                
                success = True                                                         
                # complex_ingredients = (self.extract_complex_ingredients() | self.set_category).invoke(state) 
                complex_ingredients = self.extract_complex_ingredients().invoke(state) 
                break
            except Exception as exc:
                self.LogException(exc, f"Error decoding JSON for .")
                success = False
        if not success:
            raise Exception(f"Failed to extract Complex Ingredients for  {self.num_extraction_tries} times")
                        
        document = Document(page_content=json.dumps(complex_ingredients, ensure_ascii=False), metadata=state['input'].metadata)         
        return document

    def extract_complex_ingredients(self)->Runnable:
        return (
                self.extraction_prompt 
                | self.debugger.Runnable_PrintStructureWithLabel("extraction Prompt")
                | self.llm
                | self.debugger.Runnable_PrintStructureWithLabel("llm output")
                | self.clean_and_format_output 
                | self.validate_recipe)
        
    def clean_and_format_output(self, string):
        # Assuming original_text is your input string
        cleaned_string = re.sub(r'<think>[\s\S]*?</think>', '', string, flags=re.IGNORECASE).strip()
        cleaned_string = re.sub(r'(\r\n|\n|\r)', '', cleaned_string)
        cleaned_string = re.sub(r'\s+', ' ', cleaned_string)
        return cleaned_string 
    
    def validate_recipe(self, recipe):
        errors = []
        jsondata = json.loads(recipe)
        # Check top-level keys
        if 'recipe_name' not in jsondata or not isinstance(jsondata['recipe_name'], str):
            errors.append("Missing or invalid 'recipe_name'")

        if 'ingredients' not in jsondata or not isinstance(jsondata['ingredients'], list):
            errors.append("Missing or invalid 'ingredients' (must be a list)")

        else:
            for i, ing in enumerate(jsondata['ingredients']):
                if 'name' not in ing or not isinstance(ing['name'], str):
                    errors.append(f"Ingredient {i}: missing or invalid 'name'")
                if 'weight' not in ing or not isinstance(ing['weight'], (int, float)):
                    errors.append(f"Ingredient {i}: missing or invalid 'weight'")
                if 'category' not in ing or not isinstance(ing['category'], str):
                    errors.append(f"Ingredient {i}: missing or invalid 'category'")
                if 'quantity' in ing and ing['quantity'] is not None and not isinstance(ing['quantity'], (int, float)):
                    errors.append(f"Ingredient {i}: 'quantity' must be number or null")
                if 'unit' in ing and ing['unit'] is not None and not isinstance(ing['unit'], str):
                    errors.append(f"Ingredient {i}: 'unit' must be string or null")
                
        if len(errors) != 0:
            raise ValueError(f"Invalid json: {', '.join(errors)}")

        return jsondata

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
                item = ingredient.model_copy(update={'name' : ingredient.name.lower()})                
                self.ingredient_list.append(item)
            else:                
                ingredient.category = self.get_category(ingredient)
                self.LogMessage(f"Ingredient on the list: {ingredient.name} -> {ingredient.category}")

        return complexIngredientList
    
    def is_ingredient_on_list(self, ingredient):
        is_on_list = False
        for item in self.ingredient_list:
            if ingredient.name.lower() == item.name:
                ingredient.category = item.category            
                is_on_list = True
                break
        return is_on_list
    
    def select_category(self)->Runnable:
        """ select one of the following categories for the ingredent: Obst/Gemüse, Vegan, Milchprodukte, Tiefkühl, Sonstiges """
        return (self.category_prompt 
                | self.llm 
                | self.strOutputParser)
    
    def get_category(self, ingredient):
        for item in self.ingredient_list:
            if ingredient.name.lower() == item.name:
                return item.category
    
    def get_IngredientList(self)->list[Document]:
        docs = []
        for ingredient in self.ingredient_list:
            docs.append(Document(page_content=json.dumps(ingredient.dict(), ensure_ascii=False), metadata= {'category':ingredient.category}))
        return docs
    
    def set_IngredientList(self, ingredients:list[Document])->None:        
        for ingredient in ingredients:
            self.ingredient_list.append(Ingredient(**json.loads(ingredient.page_content)))                

    def LogMessage(self, message:str):
        self.logger.LogMessage(message, self)
        
    def LogException(self, exception:Exception, message:str = "Processing failed"):
        self.logger.LogException(exception, message, self)
        
    