from langchain_community.llms import Ollama
from Utils import store_documents_on_disk, load_documents_from_disk
from Runnables import RunnableRawIngredientExtracor, RunnableRecipeSeparator, RunnableComplexIngredientExtractor, RunnableEmbeddingStringBuilder
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
# from Logger import Logger

# ggg = Logger()
# ggg.LogException(Exception("ö"), "ä")

# Prepare Environment
modelname = "llama3.1:8b-instruct-q8_0"
embedding_modelname = "mxbai-embed-large"
llm = Ollama(model = modelname)


#################################
#   Part 1: Recipe Separation   #
#################################
pages = load_documents_from_disk('Recipes/Json/AllRecipes.json')
selected_pages = [pages[i] for i in [0, 1, 2, 4, 60, 212, 18, 19, 20, 21, 22, 23, 24, 25, 26 , 27, 28]]
state = {'input': selected_pages}


recipeSeparator = RunnableRecipeSeparator(llm)
docs = recipeSeparator.invoke(state)

store_documents_on_disk(docs, "logs/Separated.json") # --> brauche ich

#########################################
#   Part 2: Raw Ingredient Extraction   #
#########################################
pages = load_documents_from_disk("logs/Separated.json")
state = {'input': pages}


rawIngredientExtracor = RunnableRawIngredientExtracor(llm)

raw_ingredients = rawIngredientExtracor.invoke(state)
store_documents_on_disk(raw_ingredients, 'logs/RawIngredients.json') # --> Zwischenschritt

#############################################
#   Part 3: Complex Ingredient Extraction   #
#############################################
rawingredients = load_documents_from_disk('logs/RawIngredients.json')
state = {'input': rawingredients}


complexIngredientExtractor = RunnableComplexIngredientExtractor(llm)

complexIngredients = complexIngredientExtractor.invoke(state)

store_documents_on_disk(complexIngredients, 'logs/ComplexIngredients.json') # --> brauche ich

#########################################################
#   Part 4: Embedding String Generation & Embedding     #
#########################################################
pages = load_documents_from_disk("logs/Separated.json")
state = {'input': pages}


embeddingStringBuilder = RunnableEmbeddingStringBuilder(llm)

embedding_strings = embeddingStringBuilder.invoke(state)
store_documents_on_disk(embedding_strings, 'logs/RecipeEmbeddingStrings.json') # --> Zwischenschritt


embeddings = OllamaEmbeddings(model=embedding_modelname) 

# Define the path where you want to store the ChromaDB database
db_path = 'logs/Chroma'

# Use Chroma as the vector store
vector_store = Chroma.from_documents(
    documents=embedding_strings,
    embedding=embeddings,
    persist_directory=db_path
)