import json
import os

from Utils import FileLoader


fileloader = FileLoader()

def convertToJson(pages):
    for item in pages:
        item["page_content"] = json.loads(item["page_content"])    
    return pages

llamapath = "Recipes/Json"
# qwenpath = "logs/qwen3"
complexIngredients_llama3 = fileloader.load_json_from_disk(os.path.join(llamapath,"ComplexIngredients.json"))
# complexIngredients_qwen3 = fileloader.load_json_from_disk(os.path.join(qwenpath, "ComplexIngredients_qwen3.json"))

# Convert 'page_content' from JSON string to dictionary
complexIngredients_llama3 = convertToJson(complexIngredients_llama3)
# complexIngredients_qwen3 = convertToJson(complexIngredients_qwen3)
    
fileloader.store_json_on_disk(complexIngredients_llama3, os.path.join(llamapath, "ComplexIngredients_Json_original"))
# fileloader.store_json_on_disk(complexIngredients_qwen3, os.path.join(qwenpath, "ComplexIngredients_Json_qwen3"))
# Save the result to a file

print("The JSON data has been successfully converted and saved to 'converted_recipes.json'.")
