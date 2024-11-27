from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from Utils import store_documents_on_disk, load_documents_from_disk
from Runnables import RunnableRawIngredientExtracor, RunnableRecipeSeparator, RunnableComplexIngredientExtractor


# Prepare Environment
modelname = "llama3.1:8b-instruct-q4_K_S"
llm = Ollama(model = modelname)

###### Part 1 #######
## load documents from json format
# pages = load_documents_from_disk('Recipes/Json/AllRecipes.json')
# selected_pages = [pages[i] for i in [0, 1, 2, 4, 60, 212, 18, 19, 20, 21, 22, 23, 24, 25, 26 , 27, 28]]
# state = {'input': selected_pages}


# recipeSeparator = RunnableRecipeSeparator(llm)
# docs = recipeSeparator.invoke(state)

# store_documents_on_disk(docs, "logs/Separated.json")

###### Part 2 #######
# pages = load_documents_from_disk("logs/Separated.json")
# state = {'input': pages}


# rawIngredientExtracor = RunnableRawIngredientExtracor(llm)

# raw_ingredients = rawIngredientExtracor.invoke(state)
# store_documents_on_disk(raw_ingredients, 'logs/RawIngredients.json')

###### Part 3 #######

# rawingredients = load_documents_from_disk('logs/RawIngredients.json')
# state = {'input': rawingredients}


# complexIngredientExtractor = RunnableComplexIngredientExtractor(llm)

# complexIngredients = complexIngredientExtractor.invoke(state)

# store_documents_on_disk(complexIngredients, 'logs/ComplexIngredients.json')