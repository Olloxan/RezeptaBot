import unittest
from langchain_community.llms import Ollama
import pandas as pd
from io import StringIO

from Utils import Logger

# initialize logger with a timestamp
Logger("Tests/Logs/log_")
from Runnables import RunnableRecipeMapper
from VectorStore import VectorStore



class TestRunnableRecipeMapper():
    def __init__(self) -> None:
        self.setUp()

    def setUp(self) -> None:
        self.logger = Logger()
        modelname = "llama3.1:8b-instruct-q8_0"
        model = Ollama(model = modelname)
        self.mapper = RunnableRecipeMapper(model)
        self.vectorStore = VectorStore(collection_name='recipe_embeddings')

    def test_my(self):
        json_data = "{\"columns\":[\"Tag\",\"Morgens\",\"Mittags\",\"Abends\",\"Nachmittags\"],\"index\":[0,1,2,3,4,5,6,7],\"data\":[[\"Montag\",\"\",\"\",\"Brot H\\u00fcttenk\\u00e4se\",\"Joghurt-Bananen-Happen\"],[\"Dienstag\",\"Grie\\u00dfbrei mit Himbeeren\",\"Chilli sin Carne\",\"Brot H\\u00fcttenk\\u00e4se\",\"\"],[\"Mittwoch\",\"Grie\\u00dfbrei mit Himbeeren\",\"Chilli sin Carne\",\"Brot H\\u00fcttenk\\u00e4se\",\"\"],[\"Donnerstag\",\"Grie\\u00dfbrei mit Himbeeren\",\"H\\u00e4hnchen Korma\",\"Edamame salat\",\"\"],[\"Freitag\",\"Grie\\u00dfbrei mit Himbeeren\",\"H\\u00e4hnchen Korma\",\"Edamame salat\",\"\"],[\"Samstag\",\"Haferbrei\",\"Chilli sin Carne\",\"griechischer Salat\",\"\"],[\"Sonntag\",\"Haferbrei\",\"Chilli sin Carne\",\"griechischer Salat\",\"\"],[\"Montag\",\"Haferbrei\",\"\",\"\",\"\"]]}"
        data_frame_weekplan = pd.read_json(StringIO(json_data), orient="split")
        self.vectorStore.set_source("26.01.2024-3400kcal.pdf")        
        recipes_and_ingredients = self.vectorStore.get_recipes_from_last_source()
        state={}
        state['short_recipe_names'] = data_frame_weekplan
        state['recipe_names_with_ingredients'] = recipes_and_ingredients 
        meals_by_time_of_day = self.mapper.invoke(state)
        x=5

    @unittest.skip("Skipping this test because it's incomplete")
    def test_run(self):
        # json_data: --> JSON String
        data_frame_weekplan = pd.read_json(StringIO(json_data), orient="split")
       
        
        self.assertEqual(result, "test")


if __name__ == '__main__':
    kacka = TestRunnableRecipeMapper()
    kacka.test_my()