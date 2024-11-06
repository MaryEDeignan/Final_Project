import requests
import time
import json
from parsel import Selector
from random import randrange
import pandas as pd
import html

# Headers to make the request look like it's coming from a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
}

# List to hold all the recipe data
data = []

# Load recipe links from the JSON file (links we want to scrape)
with open('links/links_allrecipes.json', 'r') as json_file:
    RECIPE_LINKS = json.load(json_file)
    
    # Loop through each recipe link to scrape the data
    for link in RECIPE_LINKS.values():  
        print(f'Extracting data from link: {link}')
        
        # Initialize a dictionary to store different parts of the recipe data
        recipes_data = {
            'basic_info': {},
            'prep_data': {},
            'ingredients': [],
            'nutritions': {},
            'directions': []  
        }

        # Retry mechanism in case of request failure (up to 3 attempts)
        for attempt in range(3):
            try:
                # Send a GET request to the recipe URL
                response = requests.get(link, headers=headers, timeout=60)
                response.raise_for_status()  # Check if the response is good (status 200)
                selector = Selector(text=response.text)  # Parse the HTML content using the Selector
                break  # Exit the retry loop if the request was successful
            except requests.exceptions.RequestException as e:
                # Print error and try again after waiting a bit
                print(f'Error fetching {link}: {e}')
                time.sleep(2)  # Wait for 2 seconds before retrying
                continue  # Try again if there's an error

        # If we got a successful response (status code 200), extract the recipe data
        if response.status_code == 200:
            # Extract the title of the recipe
            title = selector.css('h1.article-heading::text').get()
            recipes_data['basic_info']['title'] = title.strip() if title else "N/A"

            # Extract the recipe category 
            category = selector.css('li.mntl-breadcrumbs__item a span.link__wrapper::text').get()
            recipes_data['basic_info']['category'] = category.strip() if category else "N/A"

            # Extract the rating of the recipe (if available)
            rating = selector.css('div.mm-recipes-review-bar__rating::text').get()
            recipes_data['basic_info']['rating'] = rating.strip() if rating else "N/A"
            
            # Extract the number of ratings 
            rating_count = selector.css('div.mm-recipes-review-bar__rating-count::text').get()
            recipes_data['basic_info']['rating_count'] = rating_count.strip('()') if rating_count else "N/A"

            # Extract preparation details (ex. time, servings)
            prep_labels = selector.css('.mm-recipes-details__label::text').getall()
            prep_values = selector.css('.mm-recipes-details__value::text').getall()

            # Clean up the labels and values and store them in a dictionary
            for label, value in zip(prep_labels, prep_values):
                key = label.lower().replace(' ', '_').replace(':', '')  # Clean the key
                recipes_data['prep_data'][key] = value.strip() if value else "N/A"

            # Extract nutritional information (ex. calories, protein)
            nutrition_rows = selector.css('.mm-recipes-nutrition-facts-summary__table-row')

            for row in nutrition_rows:
                # Extract each label and its corresponding value
                value = row.css('.mm-recipes-nutrition-facts-summary__table-cell.type--dog-bold::text').get()
                label = row.css('.mm-recipes-nutrition-facts-summary__table-cell.type--dog::text').get()
                
                # If both label and value are found, add them to the nutrition data
                if label and value:
                    recipes_data['nutritions'][label.lower()] = value.strip()

            # Extract the ingredients list
            ingredients_list = selector.css('.mm-recipes-structured-ingredients__list-item p')

            # Process each ingredient (quantity, unit, name) and build a string
            for ingredient in ingredients_list:
                quantity = ingredient.css('[data-ingredient-quantity="true"]::text').get() or ''
                unit = ingredient.css('[data-ingredient-unit="true"]::text').get() or ''
                name = ingredient.css('[data-ingredient-name="true"]::text').get() or ''

                # Combine the parts into a single string and unescape HTML characters
                ingredient_string = f"{quantity} {unit} {name}".strip()
                ingredient_string = html.unescape(ingredient_string)

                recipes_data['ingredients'].append(ingredient_string)

            # Extract the directions for the recipe
            for step in selector.css('#mm-recipes-steps__content_1-0 ol li p'):
                # Use xpath to clean up and get the step text
                recipes_data['directions'].append(step.xpath('normalize-space()').get())

            # Add the recipe data to our main list
            data.append(recipes_data)

            # Sleep for a random amount of time (1 to 3 seconds) to avoid hitting the server too hard
            time.sleep(randrange(1, 3))

# Save the extracted data to a JSON file
# Convert the list of recipes into a pandas DataFrame and then save as JSON
pd.DataFrame(data=data).to_json('recipes/recipes_allrecipes.json', orient='records')

# Print the extracted data in a nicely formatted way
print(json.dumps(data, indent=2, ensure_ascii=False))
