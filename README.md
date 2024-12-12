# Recipe Swiper

## Project Description

A more complete project description can be found  <a href="docs/Al_and_Mary_Meal_Plan_Generator.pdf">here</a> (our project proposal).

## Setting up Virtual Environment
It is recommended to set up a virtual environment to ensure you have all of the needed packages. 
The directions below work both for MacOS and Linux. 
1. Navigate to your terminal and activate an environment using the code below. 
```python
python3 -m venv recipes
```
2. Activate your environment
```python
source recipes/bin/activate
```
3. Once this enviornment is activated, run the following command to install the necessary depenencies as listed in the `requirements.txt` file.
```python
pip install -r requirements.txt
```
4. Deactivate the environment when you finish working on this project. 
```python
deactivate
```


## How to scrape your own data
If you prefer to scrape your own data instead of using the pre-scraped dataset provided in this repository, follow these steps. Note that the whole scraping process can take 2+ hours. 
1. **Clone the Repository:**  
   First, clone this repository to your local machine:
   ```python
   git clone https://github.com/MaryEDeignan/Final_Project.git
   ```
2. **Navigate to the Scraping Folder:** Go to the `scraping` directory inside the repository:
	```python 
	cd src
	cd scraping 
	```
3. **Run the Scraper Script:** To scrape the recipes and their corresponding images, execute the `scraper.py` script:
	```python
	python3 scraper.py
	```
  This will scrape 10,000+ recipes from Allrecipes.com along with their images.

5. **Saving and Using the Data:** Once the script completes, the recipe data will be saved in a JSON file located in `src/scraping/recipes` as `scraped_recipes.json`. The images will be saved in the `src/scraping/images` folder.  These images can be matched to their corresponding recipe using the image_filename field in `scraped_images.json`. Additionally, a .txt file will be created in the `src/scraping/links` folder. This file contains all the links to the scraped recipes along with the category each recipe belongs to.

## How to view and operate the interface
### 1. **Running the Application**
1. **Clone the Repository:**  *This step can be skipped if you just scraped your own data. Simply navigate to the cloned folder.*
   
   First, clone this repository to your local machine:
   ```python
   git clone https://github.com/MaryEDeignan/Final_Project.git
   ``` 
3. **Run the Application** Execute the Python script to launch the app:
	```python 
	python3 interface.py
	```
	This will start the application and open the interface in a new window.

### 2. **Interacting with the Interface**
When the application launches, the interface will display recipe cards that you can swipe through. Each card contains information about a recipe, including its title, rating, total time, and an image. If you would like more information on a recipe, you can swipe up to get more information such as ingredients, category, and nutrition information. 
#### Swipe Actions: - 
- **Swipe Right**: Click and drag the card to the right to indicate you like the recipe. You can also click the heart button on the bottom right if you have issues with swiping. The recipes you like will be saved to `preferences.csv` when you close out of the application. The last column in `preferences.csv` will have a 1 in the `like_or_dislike` column. 
- **Swipe Left**: Click and drag the card to the left to indicate you dislike the recipe. You can also click the X button on the bottom left if you have issues with swiping. The recipes you dislike will be saved to `preferences.csv` when you close out of the application. The last column in `preferences.csv` will have a 0 in the `like_or_dislike` column.
- **Swipe Up**: Click and drag upwards on the card. Additional information about the recipe will come up that can help you make the decision on whether you like it. To get back to the swiper, simply click the back button in the upper left hand corner. 

### 3. **Exiting the Interface** 
When you close the application, it will automatically save your liked and disliked recipes to the `preferences.csv` file in the `data` folder. This file contains all of the recipes you have swiped on and whether you liked or disliked it. 

## How the Recommender works
ADD INFO HERE 

## Files in the `useful_notebooks` folder
This folder serves as a record of some of the work we've done in the past, that either has not yet been automated or should not be automated.

### `data_prep.ipynb`
This file shows how we made all of our feature modifications. Some modifications are quite specific, so this process has not yet been automated. This jupyter notebook serves as a record of feature modifications.

### `report.ipynb`
This file is an initial exploration of some of our data, and avenues for measures of similarity.






