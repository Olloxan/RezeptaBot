from pydoc import Doc
from venv import logger
from langchain_core.runnables import Runnable
from langchain_core.prompts import PromptTemplate
from langchain.docstore.document import Document
from langchain_core.output_parsers import StrOutputParser

from Logger import Logger
from Runnables import RunnableDebugger as Debugger
from Utils import read_from_file

class RunnableRecipeSeparator(Runnable):
    def __init__(self, llm):
        self.llm = llm
        self.logger = Logger()
        self.debugger = Debugger()
        self.output_parser = StrOutputParser()
        self.prompt = PromptTemplate.from_template(read_from_file("Recipes/Prompts/RecipeSeparation_prompt.txt"))
        
    def invoke(self, state: dict)->list[Document]:
        """expected dict: state['input'] = List[document]"""
                
        recipes:list[Document] = []
        
        for i, document in enumerate(state['input']):   
            try:
                self.logger.LogMessage(f"Separating: document {i} from {len(state['input'])-1}")
            
                semikolon_separated_recipenames = self.separate_recipe().invoke({"input" : document})
            
                recipe_names:list[str] = semikolon_separated_recipenames.split(";")
                recipe_names = [item for item in recipe_names if item != 'leer']            
            
                # split_recipes:list[str] = [document.page_content.split(recipe_name) for recipe_name in recipe_names]
                page_content = document.page_content
                split_recipes = self.split_recipes_by_name(page_content, recipe_names)

                documents = [Document(page_content=recipe, metadata=document.metadata) for recipe in split_recipes if recipe != '']
                recipes.extend(documents)    
            except Exception as exc:
                self.logger.LogException(exc, f"Error processing document {i}. Recipe names are: {', '.join(recipe_names)}")
                recipes.append(document)
        
        return recipes

    def separate_recipe(self)->Runnable:
        return (self.prompt | self.debugger.Runnable_PrintTokencout() | self.llm | self.output_parser)
    
    def split_recipes_by_name(self, page_content:str, recipe_names:list[str])->list[str]:
        """Split the page content by the recipe names"""
        content = page_content
        stripped_recipe_names = [name.strip() for name in recipe_names]

        recipe_list = []
        if len(stripped_recipe_names)==0:
            self.logger.LogMessage("No recipe names found")
        elif len(stripped_recipe_names)==1:
            self.logger.LogMessage(f"found 1 recipe name: {stripped_recipe_names[0]}")
            recipe = f"{stripped_recipe_names[0]}\n{content.split(stripped_recipe_names[0])[1]}"
            recipe_list.append(recipe)            
        else:            
            self.logger.LogMessage(f"found {len(stripped_recipe_names)} recipe names: {', '.join(stripped_recipe_names)}")
            for name in stripped_recipe_names:
                temp = content.split(name)
                content = temp[1]
            recipes = [f"{recipename}\n{content}" for recipename, content in zip(stripped_recipe_names, temp)]
            recipe_list.extend(recipes)
                            
        return recipe_list