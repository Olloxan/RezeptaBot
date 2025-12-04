from Runnables import RunnableEmbeddingStringExtractor
from Utils import Logger, FileLoader

fileloader = FileLoader()
logger = Logger()

pages = fileloader.load_json_from_disk("Recipes/Json/ComplexIngredients.json")

state = {'input': pages}
embeddingStringExtractor = RunnableEmbeddingStringExtractor()
embedding_strings = embeddingStringExtractor.invoke(state)
x=5