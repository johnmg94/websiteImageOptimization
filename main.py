import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from urllib.parse import urljoin, urlparse
import re

# Doesn't work on SVG's
# Create output directory
# Additional feature - have the system write the correct image extensions if applicable to the html files in question
OUTPUT_DIR = "images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Function to scrape and process images
visited = []
not_visited=[]
not_visited_files=[]
regex=r'#.*'

def scrape_and_process(base_url, max_depth=3):
    # if visited is None:
    #     visited = set()
    print("Visited: ", str(visited))
    if visited is not None:
        if base_url in visited or max_depth < 0:
            return
        # If there is a match to a string that starts with '#', return
        elif (re.search(regex, base_url)):
            return
    try:
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()
        if response.status_code == 200:
            print("Scraping: ", {base_url})
            visited.append(base_url)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {base_url}: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    single_html_file_get_css(base_url, soup)
    loop_images(base_url, soup)
    # Recursively visit internal links            
    for a_tag in soup.find_all("a", href="true"):
        print("HERE")
        try:
            link_url = urljoin(base_url, a_tag["href"])
            print("LinkURL:",link_url)
        except Exception as e:
            print("Exception: ", (e))
        if link_url and is_valid_domain(base_url, link_url):
            scrape_and_process(link_url, max_depth - 1)

# Process images
def loop_images(base_url, soup_object):
    for img_tag in soup_object.find_all("img"):
        img_url = urljoin(base_url, img_tag.get("src"))
        print("REGULAR URL: ", img_url)
        if is_valid_domain(base_url, img_url):
            process_image(img_url)


def single_html_file_get_css(base_url, soup_object):
    for link_tag in soup_object.find_all("link", rel="stylesheet"):
        try:
            css_url = urljoin(base_url, link_tag.get("href"))
        except Exception as e:
            print("Exception in CSS Block: ", (e))
        print("CSS URL: ", css_url)
        if is_valid_domain(base_url, css_url):
            process_css(css_url, base_url)

# Function to process CSS files
def process_css(css_url, base_url):
    # return
    try:
        response = requests.get(css_url, timeout=10)
        response.raise_for_status()
        css_content = response.text

    #     # Find all background-image URLs using regex
        background_images = re.findall(r'background-image:\s*url\((.*?)\)', css_content)
        for bg_url in background_images:
    #         # Clean up URL and make it absolute
            bg_url = bg_url.strip('\'"')  # Remove quotes
            full_url = urljoin(base_url, bg_url)
            print("Full URL: ",full_url)
            process_image(full_url)
    except Exception as e:
        print(f"Failed to process CSS {css_url}: {e}")

# Function to check if URL belongs to the same domain
def is_valid_domain(base_url, check_url):
    return urlparse(base_url).netloc == urlparse(check_url).netloc

# Function to download, compress, and convert images
# Assumes all images are coming from the same directory - ???
def process_image(img_url):
    try:
        response = requests.get(img_url, stream=True, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        img_name = os.path.join(OUTPUT_DIR, os.path.basename(img_url).split("?")[0].split("#")[0])
        
        if not img_name.lower().endswith(".webp"):
            img_name = os.path.splitext(img_name)[0] + ".webp"
        
        img.save(img_name, "webp", quality=20)
        print(f"Saved and compressed: {img_name}")
    except Exception as e:
        print(f"Failed to process image {img_url}: {e}")


# Main execution
if __name__ == "__main__":
    start_url = input("Enter the base URL of the website: ")
    scrape_and_process(start_url)
