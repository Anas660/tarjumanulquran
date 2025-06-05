import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import random

# Base URLs for the 5 volumes
VOLUME_URLS = [
    "https://rasailomasail.net/volume/01/",
    "https://rasailomasail.net/volume/02/",
    "https://rasailomasail.net/volume/03/",
    "https://rasailomasail.net/volume/04/",
    "https://rasailomasail.net/volume/05/",
]

# Output directory
OUTPUT_DIR = "rasailomasail_html"

# Headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://rasailomasail.net/',
}

def create_output_dirs():
    """Create output directories for each volume if they don't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    for i in range(1, 6):
        vol_dir = os.path.join(OUTPUT_DIR, f"volume_{i:02d}")
        if not os.path.exists(vol_dir):
            os.makedirs(vol_dir)

def get_safe_filename(url):
    """Generate a safe filename from a URL"""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    
    # Get the last part of the path
    filename = path.split('/')[-1]
    if not filename:
        filename = 'index'
    
    # Remove any unwanted characters
    filename = ''.join(c if c.isalnum() or c in '.-_' else '_' for c in filename)
    
    return filename

def download_page(url, output_path):
    """Download a web page and save it to the specified location"""
    try:
        print(f"Downloading: {url}")
        
        # Add a small random delay to be polite to the server
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()  # Raise exception for 4XX/5XX status codes
        
        # Save the HTML content
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(response.text)
            
        print(f"Saved to: {output_path}")
        return response.text
        
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def extract_pagination_links(soup, base_url):
    """Extract pagination links from a page, including those hidden behind ellipsis"""
    pagination_links = []
    max_page_num = 1
    
    # Look for pagination elements - common patterns
    pagination = soup.find('div', class_='pagination') or soup.find('ul', class_='page-numbers') or soup.find('div', class_='nav-links')
    
    if pagination:
        # First find the highest page number to determine total pages
        for link in pagination.find_all('a'):
            href = link.get('href')
            text = link.get_text().strip()
            
            # Look for numeric page identifiers
            if text.isdigit():
                page_num = int(text)
                if page_num > max_page_num:
                    max_page_num = page_num
            
            # Also check URLs that contain page numbers
            if href and ('page=' in href or '/page/' in href):
                try:
                    # Extract page number from URL
                    if 'page=' in href:
                        page_param = href.split('page=')[1].split('&')[0]
                        if page_param.isdigit():
                            page_num = int(page_param)
                            if page_num > max_page_num:
                                max_page_num = page_num
                    elif '/page/' in href:
                        page_param = href.split('/page/')[1].split('/')[0]
                        if page_param.isdigit():
                            page_num = int(page_param)
                            if page_num > max_page_num:
                                max_page_num = page_num
                except:
                    pass
    
    # If pagination not found via class, try another approach
    if max_page_num == 1:
        # Look for links containing page numbers
        for link in soup.find_all('a'):
            href = link.get('href')
            text = link.get_text().strip()
            
            # Check if link text looks like a page number
            if text.isdigit():
                page_num = int(text)
                if page_num > max_page_num:
                    max_page_num = page_num
    
    print(f"Detected {max_page_num} total pages")
    
    # Generate URLs for all pages from 1 to max_page_num
    for page_num in range(1, max_page_num + 1):
        if page_num == 1:
            # First page is the base URL
            page_url = base_url
        else:
            # Construct URL for other pages based on the pattern
            if '?' in base_url:
                page_url = f"{base_url}&paged={page_num}"
            else:
                # Determine the right URL pattern
                if base_url.endswith('/'):
                    page_url = f"{base_url}page/{page_num}/"
                else:
                    page_url = f"{base_url}/page/{page_num}/"
        
        # Add to list, skipping the first page if it equals base_url
        if page_num == 1 and page_url == base_url:
            continue
        pagination_links.append(page_url)
    
    return pagination_links

def scrape_volume(volume_url, volume_num):
    """Scrape a complete volume including all its pages"""
    print(f"\nScraping Volume {volume_num}: {volume_url}")
    
    # Create output directory for this volume
    volume_dir = os.path.join(OUTPUT_DIR, f"volume_{volume_num:02d}")
    
    # Download the main volume page
    main_filename = os.path.join(volume_dir, "index.html")
    html_content = download_page(volume_url, main_filename)
    
    if not html_content:
        print(f"Failed to download volume {volume_num} main page. Skipping.")
        return
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract pagination links
    pagination_links = extract_pagination_links(soup, volume_url)
    print(f"Found {len(pagination_links)} pagination links")
    
    # Download each pagination page
    for i, page_url in enumerate(pagination_links, 1):
        page_filename = os.path.join(volume_dir, f"page_{i+1}.html")
        download_page(page_url, page_filename)
    
    print(f"Volume {volume_num} scraping completed: Downloaded {len(pagination_links)+1} pages total")

def main():
    """Main function to scrape all volumes"""
    print("Starting to scrape Rasail-o-Masail volumes...")
    
    # Create output directories
    create_output_dirs()
    
    # Scrape each volume
    for i, volume_url in enumerate(VOLUME_URLS, 1):
        scrape_volume(volume_url, i)
        
        # Add a longer delay between volumes
        if i < len(VOLUME_URLS):
            delay = random.uniform(3, 5)
            print(f"Waiting {delay:.1f} seconds before next volume...")
            time.sleep(delay)
    
    print("\nScraping completed! All volumes have been downloaded.")

if __name__ == "__main__":
    main()