import os
import requests
import time
import json
import tqdm
from parsel import Selector
from random import randrange
import pandas as pd
import html
from typing import Set

# Headers to mimic a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
}

# Global data storage
data = []

# Ensure directories exist
os.makedirs('images', exist_ok=True)
os.makedirs('links', exist_ok=True)

def fetch_html(url: str) -> Selector:
    '''Fetches the HTML content from a webpage and prepares it for further use.

    Arguments:
    url (str): Address of the webpage to fetch.

    Output:
    Selector: Tool to work with the HTML content of the webpage. 
              Returns None if it can't fetch the webpage after 3 tries.
    '''
    for attempt in range(3):  # Retry mechanism, attempts up to 3 times
        try:
            #print(f"Attempting to fetch URL: {url}")  
            response = requests.get(url, headers=headers, timeout=30)  # Send GET request with a 30-second timeout
            response.raise_for_status()  # Raise HTTPError for bad responses (e.g., 404, 500)
            print(f"Successfully fetched: {url}")  # Print message for success
            return Selector(text=response.text)  # Return HTML content as a Parsel Selector
        except requests.exceptions.RequestException as e:  # Handling request exceptions
            print(f"Error fetching {url}: {e}")  # Logging the error
            time.sleep(2)  # Wait 2 seconds before retrying
    # If all attempts fail, return None
    return None

def get_category_links(main_url: str) -> Set[str]:
    '''Finds and collects links to different categories from the main A-Z recipes page.

    Arguments:
    main_url (str): The address of the main page to scrape.

    Output:
    Set[str]: A collection of category links found on the page. 
              Returns an empty set if something goes wrong.
    '''
    # Initializing empty set to store category links
    category_links = set()
    try:
        # Fetch the HTML content of the main page
        selector = fetch_html(main_url)   
        if selector:
            # Extract all href attributes from the specified CSS selector, this is finding links inside a list structure
            category_links = set(
                selector.css('ul.loc.mntl-link-list li a::attr(href)').getall()
            )
    except Exception as e:
        # printing any error messages
        print(f"An error occurred while scraping categories: {e}")
    # Return the category links, or an empty set if no links were found
    return category_links



def get_recipe_links_from_category(category_url: str) -> Set[str]:
    '''Collects all recipe links from a category page and any additional pages found.

    Arguments:
    category_url (str): Address of the category page to scrape.

    Output:
    Set[str]: A collection of recipe links from the category page and any following pages. 
    '''
    # Creating empty set to store unique recipe links
    recipe_links = set()

    # Start with first page
    page = 1

    while True:  # Continue looping until there are no more pages
        try:
            # Fetch the HTML content of the current category page
            selector = fetch_html(category_url)
            # If no content is returned, exit the loop
            if not selector:
                break
            # Extract all recipe links on the current page using a CSS selector
            links_on_page = selector.css(
                'div.card-list a.mntl-card-list-items::attr(href)'
            ).getall()
            # Add the recipe links to the set to ensure only unique recipe links added
            recipe_links.update((recipe_url, category_url) for recipe_url in links_on_page)
            # Find the link to the next page in the pagination
            next_page = selector.css('a[aria-label="Next"]::attr(href)').get()
            # If there's no "Next" link, exit the loop (last page reached)
            if not next_page:
                break
            # Update the URL to scrape the next page
            category_url = next_page
            page += 1  # Increment the page count for tracking
            # Pause for a random amount of time
            time.sleep(randrange(3, 6))
        except Exception as e:
            # Logging any errors
            print(f"An error occurred: {e}")
            break
    # Return set of collected recipe links
    return recipe_links

def extract_recipe_data(recipe_url: str, category_url: str) -> dict:
    '''Scrapes recipe information from a given recipe url.

    Arguments:
    recipe_url (str): The URL of the recipe page to scrape.

    Output:
    dict: A dictionary with the following information:
        - 'basic_info': A dictionary with basic recipe infomation including:
            - 'title' (str): The title of the recipe.
            - 'category' (str): The category of the recipe.
            - 'rating' (str): The average rating of the recipe.
            - 'rating_count' (str): The number of ratings received.
        - 'prep_data': A dictionary of preparation-related data (e.g., cook time, total time).
        - 'ingredients': A list of ingredients with quantities, units, and names.
        - 'nutritions': A dictionary of nutritional information (e.g., calories, fat).
        - 'directions': A list of step-by-step cooking instructions.
        - 'image_filename': The name of the recipe image file if downloaded; "N/A" if no image is available.

    Notes:
    - If the recipe cannot be scraped, the function will return `None`.
    - The image is downloaded and saved in the `images` folder if available.
    '''

    # Print the current URL being scraped
    print(f"Scraping recipe data from: {recipe_url}")
    # Fetch the HTML content of the recipe page using the fetch_html function
    selector = fetch_html(recipe_url)
    # If no content is returned, exit the function and return None
    if not selector:
        return None

    recipes_data = {
        'basic_info': {},
        'prep_data': {},
        'ingredients': [],
        'nutritions': {},
        'directions': [],
        'image_filename': None,
        'category_url': category_url  # Store the category URL for the recipe
    }

    # Extract basic information
    title = selector.css('h1.article-heading::text').get()
    recipes_data['basic_info']['title'] = title.strip() if title else "N/A"
    category = selector.css('li.mntl-breadcrumbs__item a span.link__wrapper::text').get()
    recipes_data['basic_info']['category'] = category.strip() if category else "N/A"
    rating = selector.css('div.mm-recipes-review-bar__rating::text').get()
    recipes_data['basic_info']['rating'] = rating.strip() if rating else "N/A"
    rating_count = selector.css('div.mm-recipes-review-bar__rating-count::text').get()
    recipes_data['basic_info']['rating_count'] = rating_count.strip('()') if rating_count else "N/A"

    # Extract preparation data
    prep_labels = selector.css('.mm-recipes-details__label::text').getall()
    prep_values = selector.css('.mm-recipes-details__value::text').getall()
    for label, value in zip(prep_labels, prep_values):
        key = label.lower().replace(' ', '_').replace(':', '')
        recipes_data['prep_data'][key] = value.strip() if value else "N/A"

    # Extract nutrition data
    nutrition_rows = selector.css('tr.mm-recipes-nutrition-facts-summary__table-row')

    # Iterate through each row in the nutrition table
    for row in nutrition_rows:
        value = row.css('td.mm-recipes-nutrition-facts-summary__table-cell.text-body-100-prominent::text').get()
        label = row.css('td.mm-recipes-nutrition-facts-summary__table-cell.text-body-100::text').get()
        if label and value:
            recipes_data['nutritions'][label.strip().lower()] = value.strip()


    # Extract ingredients
    ingredients_list = selector.css('.mm-recipes-structured-ingredients__list-item p')
    for ingredient in ingredients_list:
        quantity = ingredient.css('[data-ingredient-quantity="true"]::text').get() or ''
        unit = ingredient.css('[data-ingredient-unit="true"]::text').get() or ''
        name = ingredient.css('[data-ingredient-name="true"]::text').get() or ''
        ingredient_string = f"{quantity} {unit} {name}".strip()
        recipes_data['ingredients'].append(html.unescape(ingredient_string))

    # Extract directions
    recipes_data['directions'] = [
        step.xpath('normalize-space()').get() 
        for step in selector.css('#mm-recipes-steps__content_1-0 ol li p')
    ]

    # Extract and download image
    img_tag = selector.css('div.primary-image__media img::attr(src)').get()
    if img_tag:
        try:
            image_name = img_tag.split('/')[-1]
            image_path = os.path.join('images', image_name)
            img_response = requests.get(img_tag, headers=headers)
            img_response.raise_for_status()
            with open(image_path, 'wb') as img_file:
                img_file.write(img_response.content)
            recipes_data['image_filename'] = image_name
        except requests.exceptions.RequestException as e:
            print(f"Error downloading image {img_tag}: {e}")
    else:
        recipes_data['image_filename'] = "N/A"

    return recipes_data

def scrape_allrecipes(txt_file="links/links.txt"):
    '''Scrapes recipe data from AllRecipes categories and saves the results to a JSON file.

    Arguments:
    txt_file (str): The path to the file where recipe links are stored. 
                    If the file doesn't exist or is empty, it will be generated.

    Output:
    - Saves the scraped recipe data as a JSON file in the `recipes/scraped_recipes.json` path.
    - Updates or creates the `txt_file` with recipe links if necessary.
    '''
    global data

    all_recipe_links = set()

    if not os.path.exists(txt_file) or os.stat(txt_file).st_size == 0:
        print(f"{txt_file} does not exist or is empty. Generating recipe links.")
        
        # URL for the main AllRecipes A-Z categories page
        main_url = "https://www.allrecipes.com/recipes-a-z-6735880"
        
        # Get all category links from the main A-Z page
        category_links = get_category_links(main_url)
        print(f"Found {len(category_links)} categories.")
        
        # For each category, extract all recipe links
        for category_link in category_links:
            recipe_links = get_recipe_links_from_category(category_link)
            print(f"Found {len(recipe_links)} recipes in category: {category_link}")
            all_recipe_links.update(recipe_links)

        all_recipe_links = set(list(all_recipe_links))

        # Add recipe links to the .txt file
        with open(txt_file, 'w') as file:
            for recipe_url, category_url in all_recipe_links:
                file.write(f"{recipe_url}\t{category_url}\n")  # Store as tab-separated values
    else:
        print(f"Loading links from {txt_file}")
        with open(txt_file, 'r') as file:
            all_recipe_links = set()
            for line in file.readlines():
                parts = line.strip().split("\t")
                if len(parts) == 2:  # Ensure the line contains exactly two parts
                    all_recipe_links.add(tuple(parts))

        all_recipe_links = set(list(all_recipe_links))

    # Convert set to list to use with tqdm
    recipe_links = list(all_recipe_links)

    # Use tqdm to display a progress bar for the recipe scraping process
    with tqdm.tqdm(total=len(recipe_links), desc="Scraping recipes", ncols=100) as pbar:
        # Loop through the selected recipe links and scrape data for each recipe
        for recipe_url, category_url in recipe_links:
            recipe_data = extract_recipe_data(recipe_url, category_url)  # Pass both recipe_url and category_url
            if recipe_data:
                data.append(recipe_data)  # Add the scraped recipe data to the global list
            pbar.update(1)  # Update the progress bar by 1 step

    # Save all scraped recipes to JSON file
    pd.DataFrame(data).to_json('recipes/scraped_recipes.json', orient='records')


if __name__ == "__main__":
    # Call the scrape_allrecipes function
    scrape_allrecipes()