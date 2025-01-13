import unittest
from langchain_community.llms import Ollama
import pandas as pd
from io import StringIO
from Utils import Logger
from Runnables import RunnableRecipeMapper
from VectorStore import VectorStore



class TestRunnableRecipeMapper():
    def __init__(self) -> None:
        self.setUp()

    def setUp(self) -> None:
        self.logger = Logger()
        self.logger.Set_log_file_location("Tests/Logs/log_")
        modelname = "llama3.1:8b-instruct-q4_K_S"
        model = Ollama(model = modelname)
        self.mapper = RunnableRecipeMapper(model)
        self.vectorStore = VectorStore(collection_name='recipe_embeddings')

    def test_my(self):
        json_data = "{\"columns\":[\"Tag\",\"Morgens\",\"Mittags\",\"Abends\",\"Nachmittags\"],\"index\":[0,1,2,3,4,5,6,7],\"data\":[[\"Montag\",\"\",\"\",\"\",\"\"],[\"Dienstag\",\"\",\"\",\"\",\"\"],[\"Mittwoch\",\"\",\"\",\"\",\"\"],[\"Donnerstag\",\"\",\"\",\"\",\"\"],[\"Freitag\",\"OATS MIT FRÜCHTEN\",\"Parmesankartoffeln\",\"Paprika mit Reis\",\"Joghurt mit Kokosnuss\"],[\"Samstag\",\"OATS MIT FRÜCHTEN\",\"Parmesankartoffeln\",\"Paprika mit Reis\",\"Joghurt mit Kokosnuss\"],[\"Sonntag\",\"OATS MIT FRÜCHTEN\",\"Parmesankartoffeln\",\"Ofen-Kartoffel Thunfisch\",\"Joghurt mit Kokosnuss\"],[\"Montag\",\"OATS MIT FRÜCHTEN\",\"Parmesankartoffeln\",\"Ofen-Kartoffel Thunfisch\",\"Joghurt mit Kokosnuss\"]]}"
        data_frame_weekplan = pd.read_json(StringIO(json_data), orient="split")
        self.vectorStore.set_source("26.01.2024-3400kcal.pdf")        
        recipes_and_ingredients = self.vectorStore.get_recipes_from_last_source()
        state={}
        state['short_recipe_names'] = data_frame_weekplan
        state['recipe_names_with_ingredients'] = recipes_and_ingredients 
        meals_by_time_of_day = self.mapper.invoke(state)
        x=5

    # @unittest.skip("Skipping this test because it's incomplete")
    # def test_run(self):
    #     # json_data: --> JSON String
    #     data_frame_weekplan = pd.read_json(StringIO(json_data), orient="split")
       
        
    #     self.assertEqual(result, "test")


if __name__ == '__main__':
    kacka = TestRunnableRecipeMapper()
    kacka.test_my()