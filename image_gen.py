import requests
import json
import pandas as pd
import os

#  "key": "sIuz2f2KCIt1XxnvHKsbcD14zlggLMoDUE4zUmVb33B3qyQNr6PrB8aS7RLh"
# loding dataframe 
df = pd.read_csv("data/recipe_data.csv")

# folder to save the images
folder_path = "generated_images"  

# creating  folder if it doesn't exist
os.makedirs(folder_path, exist_ok=True)

# only doing 5 images now for testing
for idx, row in df.head(5).iterrows():
    recipe_title = row["title"]  # column name is "title"
    recipe_directions = row["directions"]  # column name for directions is "directions" - not using currently
    
    # Combine title and directions for a more detailed promt - only using title currently
    prompt = f"{recipe_title}"  # {recipe_directions}

    url = "https://stablediffusionapi.com/api/v3/text2img"

    payload = json.dumps({
        "key": "sIuz2f2KCIt1XxnvHKsbcD14zlggLMoDUE4zUmVb33B3qyQNr6PrB8aS7RLh",  # change to your own api key
        "prompt": prompt, 
        "negative_prompt": None,
        "width": 512,
        "height": 512,
        "samples": 1,
        "num_inference_steps": 20,
        "seed": None,
        "guidance_scale": 7.5,
        "safety_checker": "yes",
        "multi_lingual": "no",
        "panorama": "no",
        "self_attention": "no",
        "upscale": "no",
        "embeddings_model": None,
        "webhook": None,
        "track_id": None
    })

    headers = {
        'Content-Type': 'application/json'
    }


    # sending the POST request
    response = requests.post(url, headers=headers, data=payload)

    # getting the response data
    response_data = response.json()

    if response_data.get('status') == 'success':
        # getting URL from the response
        image_url = response_data['output'][0] 

        # downloading image using the image URL
        image_response = requests.get(image_url)

        # saving the image to folder
        if image_response.status_code == 200:
            # creating filename based on the title and saving it in folder
            image_filename = os.path.join(folder_path, f"{recipe_title}.png")
            with open(image_filename, "wb") as f:
                f.write(image_response.content)
            print(f"Image for '{recipe_title}' saved successfully!")
        else:
            print(f"Failed to download image for '{recipe_title}'. Status code: {image_response.status_code}")
    else:
        print(f"Error generating image for '{recipe_title}': {response_data.get('message', 'Unknown error')}")
