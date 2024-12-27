import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from urllib.parse import urljoin, urlparse
import re

# Doesn't work on SVG's***
# Directory to store downloaded images
OUTPUT_DIR = "images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Track visited URLs to prevent duplicates
visited = []
not_visited=[]
not_visited_files=[]
# Regular expression to ignore links starting with a '#'
regex=r'#.*'

def scrape_and_process(base_url, quality, max_depth=3):
    """
    Scrape a website recursively to a specified depth, downloading and processing images and CSS resources.

    Parameters:
    - base_url (str): The starting URL for scraping.
    - max_depth (int): Maximum depth for recursive scraping. Default is 3.
    - quality (int): Between 0 and 100
    """
    if visited is not None:
        if base_url in visited or max_depth < 0:
            return
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

    # Parse HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Process CSS and images using two functions defined outside of this function block
    single_html_file_get_css(base_url, soup, quality)
    loop_images(base_url, soup, quality)

    # Recursively visit internal links of a single HTML page. Then traverses each of those links. This function is depth-first
    for a_tag in soup.find_all("a", href="true"):
        print("HERE")
        try:
            link_url = urljoin(base_url, a_tag["href"])
            print("LinkURL:",link_url)
        except Exception as e:
            print("Exception: ", (e))
        if link_url and is_valid_domain(base_url, link_url):
            scrape_and_process(link_url, quality, max_depth - 1)

# Process images
def loop_images(base_url, soup_object, quality):
    """
    Process all images in a given HTML page.

    Parameters:
    - base_url (str): The base URL of the page.
    - soup_object (BeautifulSoup): Parsed HTML content.
    - quality (int): Between 0 and 100
    """
    for img_tag in soup_object.find_all("img"):
        img_url = urljoin(base_url, img_tag.get("src"))
        print("REGULAR URL: ", img_url)
        if is_valid_domain(base_url, img_url):
            process_image(img_url, quality)


def single_html_file_get_css(base_url, soup_object, quality):
    """
    Process CSS files linked in the HTML page.

    Parameters:
    - base_url (str): The base URL of the page.
    - soup_object (BeautifulSoup): Parsed HTML content.
    - quality (int): Between 0 and 100
    """
    for link_tag in soup_object.find_all("link", rel="stylesheet"):
        try:
            css_url = urljoin(base_url, link_tag.get("href"))
        except Exception as e:
            print("Exception in CSS Block: ", (e))
        print("CSS URL: ", css_url)
        if is_valid_domain(base_url, css_url):
            process_css(css_url, base_url, quality)

# Function to process CSS files
def process_css(css_url, base_url, quality):
    """
    Process background images defined in CSS files.

    Parameters:
    - css_url (str): The URL of the CSS file.
    - base_url (str): The base URL of the page.
    - quality (int): Between 0 and 100
    """
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
            process_image(full_url, quality)
    except Exception as e:
        print(f"Failed to process CSS {css_url}: {e}")


def is_valid_domain(base_url, check_url):
    """
    Check if a URL belongs to the same domain as the base URL.

    Parameters:
    - base_url (str): The base URL of the page.
    - check_url (str): The URL to check.
    - quality (int): Between 0 and 100

    Returns:
    - bool: True if the URLs belong to the same domain, False otherwise.
    """
    return urlparse(base_url).netloc == urlparse(check_url).netloc

def process_image(img_url, quality):
    """
    Download, compress, and save an image as a .webp file.

    Parameters:
    - img_url (str): The URL of the image to process.
    - quality (int): Between 0 and 100
    """
    try:
        response = requests.get(img_url, stream=True, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        # Generate file name and ensure .webp extension
        img_name = os.path.join(OUTPUT_DIR, os.path.basename(img_url).split("?")[0].split("#")[0])
        
        if not img_name.lower().endswith(".webp"):
            img_name = os.path.splitext(img_name)[0] + ".webp"
        
        # Save and compress the imag
        img.save(img_name, "webp", quality)
        print(f"Saved and compressed: {img_name}")
    except Exception as e:
        print(f"Failed to process image {img_url}: {e}")


# Main execution
if __name__ == "__main__":
    start_url = input("Enter the base URL of the website: ")
    quality = input("Enter the quality of the image: ")
    scrape_and_process(start_url, quality)
