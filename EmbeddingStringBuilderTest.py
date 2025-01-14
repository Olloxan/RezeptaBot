from langchain_community.llms import Ollama
from Runnables import RunnableEmbeddingStringBuilder
from Utils import Logger, FileLoader

class TestRunnableEmbeddingStringBuilder():
    def __init__(self) -> None:
        self.setUp()

    def setUp(self) -> None:
        self.logger = Logger()
        self.logger.Set_log_file_location("Tests/Logs/log_")
        modelname = "llama3.1:8b-instruct-q4_K_S"
        model = Ollama(model = modelname)
        self.mapper = RunnableEmbeddingStringBuilder(model)
        self.fileLoader = FileLoader()

    def test_run(self):
        all_recipes_separated = self.fileLoader.load_documents_from_disk("Recipes/Json/AllRecipes_separated.json")
        temp_recipes = [all_recipes_separated[i] for i in [0,1]] 
        output = self.mapper.invoke({'input':temp_recipes})
        x=5

if __name__ == '__main__':
    kacka = TestRunnableEmbeddingStringBuilder()
    kacka.test_run()