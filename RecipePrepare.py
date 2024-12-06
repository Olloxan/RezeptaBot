from langchain_community.llms import Ollama
from langchain_core.runnables import RunnableAssign
from Utils import store_documents_on_disk, load_documents_from_disk
from Runnables import RunnableRawIngredientExtracor, RunnableRecipeSeparator, RunnableComplexIngredientExtractor, RunnableEmbeddingStringBuilder
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from Logger import Logger

logger = Logger()
# ggg.LogException(Exception("ö"), "ä")

# Prepare Environment
modelname = "llama3.1:8b-instruct-q8_0"
embedding_modelname = "mxbai-embed-large"
llm = Ollama(model = modelname)


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
pages = load_documents_from_disk("Recipes/Json/AllRecipes_separated.json")
ingredients = load_documents_from_disk("Recipes/Json/IngredientList.json")
 
rawIngredientExtracor = RunnableRawIngredientExtracor(llm)
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
            # complexIngredient = (rawIngredientExtracor | complexIngredientExtractor).invoke(state)            
            state['input'] = rawIngredientExtracor.invoke(state)            
            complexIngredient = complexIngredientExtractor.invoke(state)            
            success = True
            break
        except Exception as exc:
            logger.LogException(exc, f"Error processing document {i}. Source is: {document.metadata['source']}, page: {document.metadata['page']}")            
            success = False
            
    if success == False:
        logger.LogException(Exception(f"Failed to separate document. Source: {document.metadata['source']}, page: {document.metadata['page']}"), f"Processing failed 5 times. Continuing")
        store_documents_on_disk(complexIngredientExtractor.get_IngredientList(), 'logs/Ingredients.json') # --> Zwischenschritt
    complexIngredients.append(complexIngredient)
    
    if i % 50 == 0:
        logger.LogMessage(f"Storing documents on disk. Document {i} of {len(pages) - 1}")
        store_documents_on_disk(complexIngredients, f"logs/ComplexIngredients_{i}.json") # --> Zwischenschritt
        store_documents_on_disk(complexIngredientExtractor.get_IngredientList(), f"logs/Ingredients_{i}.json") # --> Zwischenschritt
    
store_documents_on_disk(complexIngredients, 'logs/ComplexIngredients.json') # --> Zwischenschritt
store_documents_on_disk(complexIngredientExtractor.get_IngredientList(), 'logs/Ingredients.json') # --> Zwischenschritt


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

logger.LogMessage(f"Storing embeddings in Chromadb at {db_path}")

# Use Chroma as the vector store
vector_store = Chroma.from_documents(
    documents=embedding_strings,
    embedding=embeddings,
    persist_directory=db_path, 
    collection_name='recipe_embeddings'
)