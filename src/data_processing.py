import pandas as pd
import nltk
nltk.download('averaged_perceptron_tagger')
nltk.download('punkt')
import json

def open_json(file_path: str):
    with open(file_path, 'r') as file:
        return json.load(file)

def count_ingredients(ingredients_list: list) -> int:
    '''    
    Count the number of ingredients in a given recipe.

    Arguments:
    ingredients_list (list): A list of ingredient strings.

    Returns:
    int: The count of non-empty ingredient strings. Returns 0 if the input list is empty.'''
    
    if ingredients_list:  # Check if the list is not empty
        # Counting non-empty strings in the list
        return sum(1 for ingredient in ingredients_list if ingredient.strip())  
    return 0  # Return 0 for empty lists

def count_verbs(text):
    tokens = nltk.word_tokenize(text)
    pos_tags = nltk.pos_tag(tokens)
    return sum(1 for word, pos in pos_tags if pos.startswith('VB'))