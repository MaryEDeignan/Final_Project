# Final_Project

## Project Description

A more complete project description can be found...

## Setting up Virtual Environment
It is recommended to set up a virtual environment to ensure you have all of the needed packages. 
The directions below work both for MacOS and Linux. 
1. Navigate to your terminal and activate an environment named
```python
python3 -m venv recipes
```
2. Activate you environment
```python
source recipes/bin/activate
```
3. Once this enviornment is activated, run the following command to install the necessary depenencies as listed in the `requirements.txt` file.
```python
pip install -r requirements.txt
```
4. Deactivate the environemnt when you finish. When you are done working on this project, make sure you deactivate the virtual environment.
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
	cd scraping 
	```
3. **Run the Scraper Script:** To scrape the recipes and their corresponding images, execute the `scraper.py` script:
	```python
	python3 scraper.py
	```
  This will scrape 10,000+ recipes from allrecipes.com along with their images.

5. **Saving and Using the Data:** Once the script completes, the recipe data will be saved in a JSON file located in `scraping/recipes` as `scraped_recipes.json`. The images will be saved in the `scraping/images` folder.  These images can be matched to their corresponding recipe using the image_filename field in `scraped_images.json`. Additionally, a .txt file will be created in the `scraping/links` folder. This file contains all the links to the scraped recipes along with the category each recipe belongs to.

## How to view and operate the Interface
### 1. **Running the Application**
1. **Clone the Repository:**  *This step can be skipped if you scraped your own data*
   
   First, clone this repository to your local machine:
   ```python
   git clone https://github.com/MaryEDeignan/Final_Project.git
   ``` 
3. **Run the Application** Execute the Python script to launch the app:
	```python 
	python3 pyqt5.py
	```
	This will start the application and open the interface in a new window.

### 2. **Interacting with the Interface**
When the application launches, the interface will display recipe cards that you can swipe through. Each card contains information about a recipe, including its title, rating, total time, and an image.
#### Swipe Actions: - 
- **Swipe Right**: Click and drag the card to the right to indicate you like the recipe. The recipes you like will be saved to `liked_recipes.csv` when you close out of the application. 
- **Swipe Left**: Click and drag the card to the left to indicate you dislike the recipe. The recipes you dislike will be saved to `disliked_recipes.csv` when you close out of the application. 

### 3. **Exiting the Interface** 
When you close the application, it will automatically save your liked and disliked recipes to the corresponding .csv files. If you want to manually save the data at any time, you can click the exit button, and the data will be exported to the specified CSV files. Currently, the data is overwritten every time you open the app and use it again.





