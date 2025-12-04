import json

filename1 = "./importantData/testjson1.txt"
filename2 = "./importantData/testjson2.txt"

with open(filename1, "r", encoding="utf-8") as f1, open(filename2, "r", encoding="utf-8") as f2:
    data1 = json.load(f1)
    data2 = json.load(f2)


for i in range(len(data1)): 
    ingredients1 = data1[i]["page_content"]["ingredients"]
    ingredients2 = data2[i]["page_content"]["ingredients"]

    # normalize_quantity_unit(ingredients1, ingredients2)
    for ing1, ing2 in zip(ingredients1, ingredients2):
        quantity1, unit1 = ing1["quantity"], ing1["unit"]
        quantity2, unit2 = ing2["quantity"], ing2["unit"]

        def are_not_null(q, u):
            return q is not None and u is not None

        # Regel anwenden
        if are_not_null(quantity1, unit1) and not are_not_null(quantity2, unit2):
            ing2["quantity"], ing2["unit"] = quantity1, unit1
        elif are_not_null(quantity2, unit2) and not are_not_null(quantity1, unit1):
            ing1["quantity"], ing1["unit"] = quantity2, unit2
        elif (quantity1 is None) != (unit1 is None):
            ing1["quantity"], ing1["unit"] = None, None
        elif (quantity2 is None) != (unit2 is None):
            ing2["quantity"], ing2["unit"] = None, None