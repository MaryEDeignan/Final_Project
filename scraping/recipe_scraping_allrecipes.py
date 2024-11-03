import requests
import time
import json
from parsel import Selector
from random import randrange
import pandas as pd
import html

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
}

data = []

# Load recipe links from the JSON file
with open('links/links_allrecipes.json', 'r') as json_file:
    RECIPE_LINKS = json.load(json_file)
    
    # Iterate over the links
    for link in RECIPE_LINKS.values():  # Assuming link is a string (URL)
        print(f'Extracting data from link: {link}')
        recipes_data = {
            'basic_info': {},
            'prep_data': {},
            'ingredients': [],
            'nutritions': {},
            'directions': []  
        }

        for attempt in range(3):  # Retry mechanism
            try:
                # Fetch the HTML content
                response = requests.get(link, headers=headers, timeout=60)
                response.raise_for_status()  # Raise an error for bad responses
                selector = Selector(text=response.text)
                break  # Exit the retry loop if successful
            except requests.exceptions.RequestException as e:
                print(f'Error fetching {link}: {e}')
                time.sleep(2)  # Wait before retrying
                continue  # Try again

        # Extract data if response was successful
        if response.status_code == 200:
            title = selector.css('h1.article-heading::text').get()
            recipes_data['basic_info']['title'] = title.strip() if title else "N/A"

            category = selector.css('li.mntl-breadcrumbs__item a span.link__wrapper::text').get()
            recipes_data['basic_info']['category'] = category.strip() if category else "N/A"

            rating = selector.css('div.mm-recipes-review-bar__rating::text').get()
            recipes_data['basic_info']['rating'] = rating.strip() if rating else "N/A"
            
            rating_count = selector.css('div.mm-recipes-review-bar__rating-count::text').get()
            recipes_data['basic_info']['rating_count'] = rating_count.strip('()') if rating_count else "N/A"

            prep_labels = selector.css('.mm-recipes-details__label::text').getall()
            prep_values = selector.css('.mm-recipes-details__value::text').getall()

            for label, value in zip(prep_labels, prep_values):
                key = label.lower().replace(' ', '_').replace(':', '')  # Clean key
                recipes_data['prep_data'][key] = value.strip() if value else "N/A"

            nutrition_rows = selector.css('.mm-recipes-nutrition-facts-summary__table-row')

            for row in nutrition_rows:
                value = row.css('.mm-recipes-nutrition-facts-summary__table-cell.type--dog-bold::text').get()
                label = row.css('.mm-recipes-nutrition-facts-summary__table-cell.type--dog::text').get()
                
                if label and value:
                    recipes_data['nutritions'][label.lower()] = value.strip()

            ingredients_list = selector.css('.mm-recipes-structured-ingredients__list-item p')

            for ingredient in ingredients_list:
                quantity = ingredient.css('[data-ingredient-quantity="true"]::text').get() or ''
                unit = ingredient.css('[data-ingredient-unit="true"]::text').get() or ''
                name = ingredient.css('[data-ingredient-name="true"]::text').get() or ''

                ingredient_string = f"{quantity} {unit} {name}".strip()
                ingredient_string = html.unescape(ingredient_string)

                recipes_data['ingredients'].append(ingredient_string)

            for step in selector.css('#mm-recipes-steps__content_1-0 ol li p'):
                recipes_data['directions'].append(step.xpath('normalize-space()').get())

            data.append(recipes_data)

            # Sleep to avoid overwhelming the server
            time.sleep(randrange(1, 3))

# Save the extracted data to a JSON file
pd.DataFrame(data=data).to_json('recipes/recipes_allrecipes.json', orient='records')
print(json.dumps(data, indent=2, ensure_ascii=False))
