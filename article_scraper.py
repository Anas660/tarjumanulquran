import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def extract_and_save_articles():
    # Create directory for saving article HTML files
    article_html_dir = 'article_html_files'
    os.makedirs(article_html_dir, exist_ok=True)
    
    # User agent header for requests
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Source directory containing HTML files with article links
    html_dir = "pages"
    
    # Track links to avoid duplicates
    processed_links = set()
    
    # Process each HTML file in the source directory
    for filename in os.listdir(html_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(html_dir, filename)
            
            print(f"Processing file: {filename}")
            
            # Read the HTML file
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all article links - looking for URLs with the pattern /articles/...
            article_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/articles/' in href:
                    article_links.append(href)
            
            print(f"Found {len(article_links)} article links in {filename}")
            
            # Process each article link
            for article_url in article_links:
                # Skip already processed links
                if article_url in processed_links:
                    continue
                    
                processed_links.add(article_url)
                
                try:
                    print(f"Downloading: {article_url}")
                    
                    # Download the article HTML
                    response = requests.get(article_url, headers=headers)
                    response.raise_for_status()
                    
                    # Create a safe filename from the URL
                    url_parts = urlparse(article_url)
                    article_slug = url_parts.path.split('/')[-1]
                    
                    if not article_slug:  # Handle trailing slash case
                        article_slug = url_parts.path.split('/')[-2]
                    
                    # Clean the filename to ensure it's valid
                    safe_filename = re.sub(r'[\\/*?:"<>|]', '_', article_slug)
                    if not safe_filename.endswith('.html'):
                        safe_filename += '.html'
                    
                    # Save the article HTML
                    article_file_path = os.path.join(article_html_dir, safe_filename)
                    with open(article_file_path, 'w', encoding='utf-8') as file:
                        file.write(response.text)
                    
                    print(f"Saved: {safe_filename}")
                    
                    # Be polite to the server
                    time.sleep(1)
                
                except Exception as e:
                    print(f"Error downloading {article_url}: {e}")
    
    print(f"Total articles processed: {len(processed_links)}")

if __name__ == "__main__":
    extract_and_save_articles()