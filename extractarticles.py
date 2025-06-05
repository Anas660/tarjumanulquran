import os
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

# Input and output directories
INPUT_DIR = "rasailomasail_html"  # Keep the base directory
OUTPUT_DIR = "rasailomasail_articles"  # Keep the base directory

# Headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://rasailomasail.net/',
}

def create_output_dirs():
    """Create output directory for volume 5"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    vol_dir = os.path.join(OUTPUT_DIR, "volume_05")
    if not os.path.exists(vol_dir):
        os.makedirs(vol_dir)

def get_safe_filename(title, url):
    """Generate a safe filename from an article title and URL"""
    # Try to use the last part of the URL
    url_part = url.rstrip('/').split('/')[-1]
    
    # For titles in Urdu/Arabic, use URL as base but keep length reasonable
    if re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', title):
        filename = url_part[:100]
    else:
        # For Latin text, sanitize the title
        filename = ''.join(c if c.isalnum() or c in ' -_' else '_' for c in title)
        filename = filename.replace(' ', '_')[:100]
    
    # Ensure we have a valid filename
    if not filename or filename.startswith('.'):
        filename = 'article_' + str(hash(url) % 10000)
    
    return filename + '.html'

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
        return True
        
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def extract_article_links(html_file):
    """Extract article links and titles from an HTML file"""
    try:
        with open(html_file, 'r', encoding='utf-8') as file:
            content = file.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        articles = []
        
        # Look for entry titles with the specific class structure provided
        entry_titles = soup.find_all('h2', class_='blog-entry-title')
        
        # If not found, try more general entry-title classes
        if not entry_titles:
            entry_titles = soup.find_all(['h2', 'h3'], class_=['entry-title', 'post-title'])
        
        # If still not found, try any h2 with a link
        if not entry_titles:
            entry_titles = [h2 for h2 in soup.find_all('h2') if h2.find('a', href=True)]
        
        for title_elem in entry_titles:
            link_elem = title_elem.find('a', href=True)
            if link_elem:
                title = link_elem.get_text(strip=True)
                url = link_elem['href']
                articles.append((title, url))
        
        return articles
    
    except Exception as e:
        print(f"Error extracting links from {html_file}: {e}")
        return []

def process_volume():
    """Process all HTML pages in volume 5 and extract articles"""
    volume_num = 5
    volume_dir = os.path.join(INPUT_DIR, f"volume_{volume_num:02d}")
    output_dir = os.path.join(OUTPUT_DIR, f"volume_{volume_num:02d}")
    
    print(f"\nProcessing Volume {volume_num}...")
    
    if not os.path.exists(volume_dir):
        print(f"Volume directory {volume_dir} not found. Skipping.")
        return
    
    # Get all HTML files in the volume directory
    html_files = [
        os.path.join(volume_dir, f) 
        for f in os.listdir(volume_dir) 
        if f.endswith('.html')
    ]
    
    print(f"Found {len(html_files)} HTML pages to process")
    
    # Extract article links from all pages
    all_articles = []
    
    for html_file in html_files:
        articles = extract_article_links(html_file)
        print(f"Found {len(articles)} articles in {os.path.basename(html_file)}")
        all_articles.extend(articles)
    
    # Remove duplicates (same URL)
    unique_articles = []
    seen_urls = set()
    
    for title, url in all_articles:
        if url not in seen_urls:
            unique_articles.append((title, url))
            seen_urls.add(url)
    
    print(f"Total unique articles found: {len(unique_articles)}")
    
    # Download each article
    for i, (title, url) in enumerate(unique_articles, 1):
        filename = get_safe_filename(title, url)
        output_path = os.path.join(output_dir, filename)
        
        # Skip if already downloaded
        if os.path.exists(output_path):
            print(f"[{i}/{len(unique_articles)}] Already exists: {filename}")
            continue
        
        # Download the article
        print(f"[{i}/{len(unique_articles)}] Downloading: {title}")
        download_page(url, output_path)
        
        # Add a small delay between requests
        if i < len(unique_articles):
            time.sleep(random.uniform(1, 2))

def main():
    """Main function to extract and download articles from volume 5 only"""
    print("Starting to extract and download articles from Rasail-o-Masail Volume 5...")
    
    # Create output directories
    create_output_dirs()
    
    # Process volume 5 only
    process_volume()
    
    print("\nArticle extraction and download completed for Volume 5!")

if __name__ == "__main__":
    main()