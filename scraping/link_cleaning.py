import json

# Function to clean up the URLs
def clean_url(url):
    # Preserve the 'https://' part, but replace any other '//' with a single '/'
    if url.startswith('https://'):
        url = 'https://' + url[8:].replace('//', '/')
    return url

# Read links from a JSON file
def read_links_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# Write cleaned links to a JSON file
def write_cleaned_links_json(file_path, links):
    with open(file_path, 'w') as f:
        json.dump(links, f, indent=4)

def main():
    # File paths
    input_file = 'links/links_allrecipes.json'  # Your JSON file containing the links
    output_file = 'links/cleaned_links_allrecipes.json'  # File to save cleaned links in JSON format

    # Step 1: Read JSON data
    data = read_links_json(input_file)

    # Step 2: Extract and clean the URLs
    cleaned_data = {key: clean_url(url) for key, url in data.items()}

    # Step 3: Write cleaned URLs to JSON file
    write_cleaned_links_json(output_file, cleaned_data)

    print(f"Processed {len(data)} links. Cleaned links saved to '{output_file}'.")

if __name__ == '__main__':
    main()
