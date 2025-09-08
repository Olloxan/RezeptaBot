from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_openai import OpenAI
from langchain_core.runnables import RunnableAssign
from Utils import FileLoader
from Runnables import RunnableRawIngredientExtracor, RunnableRecipeSeparator, RunnableComplexIngredientExtractor, RunnableEmbeddingStringBuilder, RunnableEmbeddingStringExtractor
from langchain_community.vectorstores import Chroma
from Utils import Logger
import os
os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11434"

logger = Logger()
fileloader = FileLoader()
# ggg.LogException(Exception("ö"), "ä")

# Prepare Environment
modelname = "llama3.1:latest"
embedding_modelname = "mxbai-embed-large"
llm = OllamaLLM(model = modelname)


#################################
#   Part 1: Recipe Separation   #
#################################
# pages = load_documents_from_disk('Recipes/Json/AllRecipes.json')
# # selected_pages = [pages[i] for i in [0, 1, 2, 4, 60, 212, 18, 19, 20, 21, 22, 23, 24, 25, 26 , 27, 28]]
# selected_pages = pages
# state = {'input': selected_pages}


# recipeSeparator = RunnableRecipeSeparator(llm)
# docs = recipeSeparator.invoke(state)

# store_documents_on_disk(docs, "Recipes/Json/AllRecipes_separated.json") # --> brauche ich

#########################################
#   Part 2: Raw Ingredient Extraction   #
#########################################
#############################################
#   Part 3: Complex Ingredient Extraction   #
#############################################
pages = fileloader.load_documents_from_disk("Recipes/Json/AllRecipes_separated.json")
ingredients = fileloader.load_documents_from_disk("Recipes/Json/IngredientList.json")
 
# rawIngredientExtracor = RunnableAssign({'input':RunnableRawIngredientExtracor(llm)})
complexIngredientExtractor = RunnableComplexIngredientExtractor(llm)
complexIngredientExtractor.set_IngredientList(ingredients)

state={}
complexIngredients = []

for i, document in enumerate(pages):
    success = True
    for j in range(5):        
        try:
            logger.LogMessage(f"Processing document {i} of {len(pages) - 1}")
            state['input'] = document
            complexIngredient = complexIngredientExtractor.invoke(state)            
            success = True
            break
        except Exception as exc:
            logger.LogException(exc, f"Error processing document {i}. Source is: {document.metadata['source']}, page: {document.metadata['page']}")            
            success = False
            
    if success == False:
        logger.LogException(Exception(f"Failed to separate document. Source: {document.metadata['source']}, page: {document.metadata['page']}"), f"Processing failed 5 times. Continuing")
        fileloader.store_documents_on_disk(complexIngredientExtractor.get_IngredientList(), 'logs/Ingredients.json') # --> Zwischenschritt
        continue
    complexIngredients.append(complexIngredient)
    
    if i % 50 == 0:
        logger.LogMessage(f"Storing documents on disk. Document {i} of {len(pages) - 1}")
        fileloader.store_documents_on_disk(complexIngredients, f"logs/ComplexIngredients_{i}.json") # --> Zwischenschritt
        fileloader.store_documents_on_disk(complexIngredientExtractor.get_IngredientList(), f"logs/Ingredients_{i}.json") # --> Zwischenschritt
    
fileloader.store_documents_on_disk(complexIngredients, 'logs/ComplexIngredients.json') # --> Zwischenschritt
fileloader.store_documents_on_disk(complexIngredientExtractor.get_IngredientList(), 'logs/Ingredients.json') # --> Zwischenschritt


##################################################################################
#   Part 4: Embedding String Generation if ComplexIngredients are not available  #
##################################################################################
# pages = fileloader.load_documents_from_disk("Recipes/Json/AllRecipes_separated.json")
# state = {'input': pages}

# embeddingStringBuilder = RunnableEmbeddingStringBuilder(llm)

# embedding_strings = embeddingStringBuilder.invoke(state)
# fileloader.store_documents_on_disk(embedding_strings, 'logs/RecipeEmbeddingStrings.json') # --> Zwischenschritt

##############################################################################
#   Part 5: Embedding String Extraction if ComplexIngredients are available  #
##############################################################################

# pages = fileloader.load_documents_from_disk("Recipes/Json/ComplexIngredients.json")
# state = {'input': pages}

# embeddingStringExtractor = RunnableEmbeddingStringExtractor()
# embedding_strings = embeddingStringExtractor.invoke(state)
# fileloader.store_documents_on_disk(embedding_strings, 'logs/RecipeEmbeddingStrings.json')

################################
#   Part 6: String Embedding   #
################################

# embeddings = OllamaEmbeddings(model=embedding_modelname) 

# # Define the path where you want to store the ChromaDB database
# db_path = 'logs/Chroma'

# logger.LogMessage(f"Chroma path {db_path}")
# logger.LogMessage(f"Start generating embeddings for {len(pages)} documents.")


# # Use Chroma as the vector store
# vector_store = Chroma.from_documents(
#     documents=embedding_strings,
#     embedding=embeddings,
#     persist_directory=db_path, 
#     collection_name='recipe_embeddings'
# )

# logger.LogMessage(f"Embeddings generated and stored in ChromaDB at {db_path}")

logger.LogMessage("Hello World")