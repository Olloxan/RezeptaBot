from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from Utils import load_documents_from_disk, read_from_file, store_raw_ingredient_lists_on_disk, store_documents_on_disk
from Runnables import RunnableRawIngredientExtracor, RunnableRecipeSeparator
from BaseModels import RawIngredientList

# Prepare Environment
modelname = "llama3.1:8b-instruct-q4_K_S"
llm = Ollama(model = modelname)

pages = load_documents_from_disk('Recipes/Json/AllRecipes.json')
selected_pages = [pages[i] for i in [60, 1, 0]]
state = {'input': selected_pages}


recipeSeparator = RunnableRecipeSeparator(llm)
docs = recipeSeparator.invoke(state)
store_documents_on_disk(docs, "logs/Separated.json")
# prompt = PromptTemplate.from_template(read_from_file("Recipes/Prompts/RawIngredientExtraction.txt"))
# rawIngredientExtracor = RunnableRawIngredientExtracor(RawIngredientList, llm, prompt)


# raw_ingredients = rawIngredientExtracor.invoke(state)
# store_raw_ingredient_lists_on_disk(raw_ingredients, 'Recipes/RawIngredients.json')