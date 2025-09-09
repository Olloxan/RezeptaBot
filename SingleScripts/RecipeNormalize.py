import json

# def normalize_quantity_unit(ingredients1, ingredients2):

filename1 = "C:/Source/RezeptaBot/logs/ComplexIngredientsInWork_llama_normalized"
filename2 = "C:/Source/RezeptaBot/logs/ComplexIngredientsInWork_qwen_normalized" 
# filename1 = "C:/Source/RezeptaBot/logs/ComplexIngredientsInWork_llama"
# filename2 = "C:/Source/RezeptaBot/logs/ComplexIngredientsInWork_qwen"
# Dateien einlesen
with open(filename1, "r", encoding="utf-8") as f1, open(filename2, "r", encoding="utf-8") as f2:
    data1 = json.load(f1)
    data2 = json.load(f2)


for i in range(len(data1)): 
    ingredients1 = data1[i]["page_content"]["ingredients"]
    ingredients2 = data2[i]["page_content"]["ingredients"]

    # normalize_quantity_unit(ingredients1, ingredients2)
    for ing1, ing2 in zip(ingredients1, ingredients2):
        q1, u1 = ing1["quantity"], ing1["unit"]
        q2, u2 = ing2["quantity"], ing2["unit"]

        def is_valid(q, u):
            return q is not None and u is not None

        # Regel anwenden
        if is_valid(q1, u1) and not is_valid(q2, u2):
            ing2["quantity"], ing2["unit"] = q1, u1
        elif is_valid(q2, u2) and not is_valid(q1, u1):
            ing1["quantity"], ing1["unit"] = q2, u2
        elif (q1 is None) != (u1 is None):
            ing1["quantity"], ing1["unit"] = None, None
        elif (q2 is None) != (u2 is None):
            ing2["quantity"], ing2["unit"] = None, None


filename1 = "C:/Source/RezeptaBot/logs/ComplexIngredientsInWork_llama_normalized"
filename2 = "C:/Source/RezeptaBot/logs/ComplexIngredientsInWork_qwen_normalized"
# Ergebnis speichern
with open(filename1, "w", encoding="utf-8") as f1, open(filename2, "w", encoding="utf-8") as f2:
    json.dump(data1, f1, indent=2, ensure_ascii=False)
    json.dump(data2, f2, indent=2, ensure_ascii=False)
