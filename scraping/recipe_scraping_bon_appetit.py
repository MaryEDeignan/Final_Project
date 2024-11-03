import requests
import time
import json
import pandas as pd
from parsel import Selector
from random import randrange

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
}

data = []

# Load recipe links from the uploaded JSON file
with open('links/links_bon_appetit.json', 'r') as json_file:
    RECIPE_LINKS = json.load(json_file)

    for link in RECIPE_LINKS.values():
        try:
            print(f'Extracting data from link: {link}')
            response = requests.get(link, headers=headers, timeout=30)
            response.raise_for_status()  # Raise an error for bad responses
            selector = Selector(text=response.text)

            recipes_data = {
                'basic_info': {},
                'prep_data': {},
                'ingredients': [],
                'nutritions': {},
                'directions': []
            }

            # Extract title
            title = selector.css('h1[data-testid="ContentHeaderHed"]::text').get()
            recipes_data['basic_info']['title'] = title.strip() if title else "N/A"

            # Extract rating
            rating = selector.css('p.RatingRating-btVmKd::text').get()
            recipes_data['basic_info']['rating'] = rating.strip() if rating else "N/A"

            # Extract prep data
            prep_info_list = selector.css('div.InfoSliceContainer-bqIWPj')  # Adjust selector as necessary
            for item in prep_info_list:
                key = item.css('p.InfoSliceKey-gHIvng::text').get()
                value = item.css('p.InfoSliceValue-tfmqg::text').get()
                if key and value:
                    cleaned_key = key.lower().replace(' ', '_').replace(':', '')
                    recipes_data['prep_data'][cleaned_key] = value.strip()

            # Specifically handle "Total Time" and "Yield" if they exist
            total_time = selector.css('p:contains("Total Time") + p::text').get()
            yield_info = selector.css('p:contains("Yield") + p::text').get()
            if total_time:
                recipes_data['prep_data']['total_time'] = total_time.strip()
            if yield_info:
                recipes_data['prep_data']['yield'] = yield_info.strip()

            # Extract nutritional information
            nutrition_items = {
                'Calories (kcal)': None,
                'Fat (g)': None,
                'Saturated Fat (g)': None,
                'Cholesterol (mg)': None,
                'Carbohydrates (g)': None,
                'Dietary Fiber (g)': None,
                'Total Sugars (g)': None,
                'Protein (g)': None,
                'Sodium (mg)': None,
            }

            nutrition_data = selector.css('div.List-iSNGTT .Description-cSrMCf')
            for item in nutrition_data:
                text = item.css('::text').get()
                if text:  # Check if text is not None
                    text = text.strip()  # Now it's safe to call strip()
                    parts = text.split()
                    key = ' '.join(parts[:-1])  # All except the last part
                    value = parts[-1]  # Last part is the value
                    if key in nutrition_items:
                        nutrition_items[key] = value.strip()

            recipes_data['nutritions'] = nutrition_items

            # Extract ingredients
            ingredients_list = selector.css('div.List-iSNGTT p.Amount-hYcAMN')
            for ingredient in ingredients_list:
                quantity = ingredient.css('::text').get() or ''
                next_elem = ingredient.xpath('following-sibling::div[1]')
                if next_elem:
                    name = next_elem.css('::text').get() or ''
                    ingredient_string = f"{quantity} {name}".strip()
                    recipes_data['ingredients'].append(ingredient_string)

            # Extract directions
            instruction_steps = selector.css('li.InstructionListWrapper-dcpygI')
            for step in instruction_steps:
                group_title = step.css('h3::text').get()
                step_title = step.css('h4::text').get()
                step_description = step.css('p::text').getall()
                full_step_description = ' '.join([desc.strip() for desc in step_description if desc.strip()])
                full_step = f"{group_title} - {step_title}: {full_step_description}"
                recipes_data['directions'].append(full_step)

            data.append(recipes_data)

            time.sleep(randrange(1, 2))  # Sleep for a random time between 1 and 2 seconds

        except Exception as e:
            print(f"An error occurred while processing {link}: {e}")

# Save the extracted data to a JSON file
pd.DataFrame(data=data).to_json('recipes/recipes_bon_appetit.json', orient='records')
print(json.dumps(data, indent=2, ensure_ascii=False))