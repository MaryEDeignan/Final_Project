# Final_Project

## How to scrape your own data
If you prefer to scrape your own data instead of using the pre-scraped dataset provided in this repository, follow these steps. Note that the whole scraping process can take 2+ hours. 
1. **Clone the Repository:**  
   First, clone this repository to your local machine:
   ```python
   git clone https://github.com/MaryEDeignan/Final_Project.git
   ```
2. **Navigate to the Scraping Folder:** Go to the `scraping` directory inside the repository:
	```python 
	cd scraping 
	```
3. **Run the Scraper Script:** To scrape the recipes and their corresponding images, execute the `scraper.py` script:
	```python
	python3 scraper.py
	```
  This will scrape 10,000+ recipes from allrecipes.com along with their images.

5. **Saving and Using the Data:** Once the script completes, the recipe data will be saved in a JSON file located in `scraping/recipes` as `scraped_recipes.json`. The images will be saved in the `scraping/images` folder.  These images can be matched to their corresponding recipe using the image_filename field in `scraped_images.json`. Additionally, a .txt file will be created in the `scraping/links` folder. This file contains all the links to the scraped recipes along with the category each recipe belongs to.
