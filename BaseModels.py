from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal


class RawIngredientList(BaseModel):
    recipe_name: str = Field('', description="Full name of the recipe")
    ingredients: List[str] = Field([], description="List of ingredients in the recipe")
    
class Ingredient(BaseModel):
    name: str                          # Name of the ingredient
    quantity: Optional[Decimal] = Field(None, gt=0)          # The amount of the ingredient, must be greater than 0
    unit: Optional[str]                          # Unit of the ingredient (e.g., Stück, Dose, Tasse)
    weight: Decimal = Field(..., ge=0)  # Optional weight in grams, must be 0 or greater
    weight_unit: str          # Optional unit for the weight (e.g., g), can be None if weight is not provided
    category: str

class ComplexIngredientList(BaseModel):
    recipe_name: str
    ingredients: List[Ingredient] = Field([])
    
