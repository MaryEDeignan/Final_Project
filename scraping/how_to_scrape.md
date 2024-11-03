
# How to Scrape Recipes

  

## Step 1: Obtaining Links
To begin the scraping process, you first need to gather links. Execute the cells in the **link_scraping.ipynb** notebook. Please note that the Allrecipes link scraper may take approximately 2 hours to complete, while the Bon Appétit scraper will run much more quickly.

You may need to modify the path (`'links/links_allrecipes.json'`) to your desired location for saving the JSON files. This will need to be changed for both the AllRecipes and Bon Appétit link scrapers and can be done by locating the following line in the code.

```python

pd.Series(list(all_recipe_links)).to_json('links/links_allrecipes.json', index=False)

```

## Step 2: Recipe Scraping
Once you have collected the links, you can proceed with scraping the recipes. Like with the link scraper, you may need to change the file paths. If you adjusted the link saving code, you will need to edit the following code to correspond to your new file location or name.

```python

with  open('links/links_bon_appetit.json', 'r') as json_file:

```

You may also want to change the name of your json output that contains the recipes or the filename. That can be changed at the bottom of the file with the following line of code:

```python

pd.DataFrame(data=data).to_json('recipes/recipes_bon_appetit.json', orient='records')

```
To run the scraper, open your terminal and navigate to the directory containing the scraper Python files and the link files. Execute the following commands to run the scrapers:


```python recipe_scraping_allrecipes.py```

```python recipe_scraping_bon_appetit.py```


### Note:
Both scrapers take a considerable amount of time to complete. It is not recommended to repeat these steps unless additional data is required.