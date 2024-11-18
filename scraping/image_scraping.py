import requests
import time
import json
from random import randrange
import os
from bs4 import BeautifulSoup

# Headers to make the request look like it's coming from a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
}

# Create a folder to save images if it doesn't already exist
if not os.path.exists('images'):
    os.makedirs('images')

# Function to get the image from the recipe URL
def get_image_from_allrecipes(recipe_url):
    response = requests.get(recipe_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the image tag with class 'primary-image__image'
    img_tag = soup.find('img', {'class': 'primary-image__image'})

    if img_tag:
        img_url = img_tag.get('src')
        if img_url:
            # If the image URL is relative, make it absolute
            if img_url.startswith('/'):
                img_url = f"https://www.allrecipes.com{img_url}"
            return img_url
    return None

# Load recipe links from the JSON file (links we want to scrape)
with open('links/cleaned_links_allrecipes_test.json', 'r') as json_file:
    RECIPE_LINKS = json.load(json_file)
    
    # Loop through each recipe link to scrape the image data
    for idx, link in RECIPE_LINKS.items():  
        print(f'Extracting image from link: {link}')
        
        # Get the image URL from the recipe page
        image_url = get_image_from_allrecipes(link)
        
        if image_url:
            # Get the image name from the URL (e.g., "8737107_Mixed-Vegetable-Curry_Brenda-Venable_4x3-f65b0efec23f4ca5b923029abe5deb45.jpg")
            image_name = image_url.split('/')[-1]
            image_path = os.path.join('images', image_name)
            
            try:
                # Download the image and save it to the 'images' folder
                img_response = requests.get(image_url, headers=headers)
                img_response.raise_for_status()  # Check if the request was successful
                
                with open(image_path, 'wb') as img_file:
                    img_file.write(img_response.content)
                
                print(f'Image saved: {image_name}')
            except requests.exceptions.RequestException as e:
                print(f'Error downloading {image_url}: {e}')
        
        # Sleep for a random amount of time (1 to 3 seconds) to avoid hitting the server too hard
        time.sleep(randrange(1, 3))

print("Image extraction complete.")
