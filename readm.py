import os
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests

def scrape_with_selenium():
    # Base URL to scrape
    base_url = "https://readmaududi.com/category/books-syed-maududi/others-books-of-maududi/"
    
    # Create directories for saving content
    main_dir = 'readmaududi_scrape'
    html_dir = os.path.join(main_dir, 'html')
    books_dir = os.path.join(main_dir, 'books')
    
    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(books_dir, exist_ok=True)
    
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-extensions")
    
    # Add user agent to appear as a regular browser
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    print("Initializing Chrome webdriver...")
    driver = webdriver.Chrome(options=chrome_options)
    
    def save_html(content, filename):
        """Save HTML content to a file"""
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)
    
    def get_safe_filename(url, title=None):
        """Create a safe filename from URL or title"""
        if title:
            # Use title if available
            safe_name = ''.join(c if c.isalnum() or c in ' -_' else '_' for c in title)
            safe_name = safe_name.strip().replace(' ', '_')
            return safe_name[:100]  # Limit length
        else:
            # Use URL path
            path = urlparse(url).path.strip('/')
            filename = path.split('/')[-1]
            if not filename:
                filename = 'index'
            return filename
    
    try:
        # Load the main page
        print(f"Loading page: {base_url}")
        driver.get(base_url)
        
        # Wait for page to load - look for common elements
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            print("Page loaded successfully!")
        except TimeoutException:
            print("Page load timed out. Proceeding with what we have...")
        
        # Sleep a bit to let any JavaScript finish executing
        time.sleep(3)
        
        # Get page content after JavaScript execution
        page_source = driver.page_source
        
        # Save the main page content
        main_filename = os.path.join(html_dir, 'main_page.html')
        save_html(page_source, main_filename)
        print(f"Saved main page as {main_filename}")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all article elements
        articles = soup.find_all('article')
        print(f"Found {len(articles)} articles on the main page")
        
        # Extract book links
        book_links = []
        for article in articles:
            # Look for title and link
            title_element = article.find(['h2', 'h3'], class_='entry-title')
            if title_element:
                link_element = title_element.find('a')
                if link_element and link_element.get('href'):
                    title = link_element.get_text(strip=True)
                    url = link_element.get('href')
                    book_links.append((url, title))
        
        print(f"Extracted {len(book_links)} book links")
        
        # Check for pagination
        pagination = soup.find('nav', class_='pagination')
        page_links = []
        
        if pagination:
            for page_link in pagination.find_all('a', class_='page-numbers'):
                href = page_link.get('href')
                if href and '#' not in href:
                    page_links.append(href)
            
            print(f"Found {len(page_links)} pagination links")
        
        # Process each pagination page
        for i, page_url in enumerate(page_links, 1):
            print(f"\nProcessing pagination page {i}: {page_url}")
            try:
                # Load the page with Selenium
                driver.get(page_url)
                
                # Wait for articles to load
                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.TAG_NAME, "article"))
                    )
                except TimeoutException:
                    print("Page load timed out. Proceeding with what we have...")
                
                # Short delay
                time.sleep(random.uniform(2, 4))
                
                # Save the page
                page_source = driver.page_source
                page_filename = os.path.join(html_dir, f'page_{i+1}.html')
                save_html(page_source, page_filename)
                print(f"Saved pagination page as {page_filename}")
                
                # Extract books from this page
                page_soup = BeautifulSoup(page_source, 'html.parser')
                page_articles = page_soup.find_all('article')
                
                for article in page_articles:
                    title_element = article.find(['h2', 'h3'], class_='entry-title')
                    if title_element:
                        link_element = title_element.find('a')
                        if link_element and link_element.get('href'):
                            title = link_element.get_text(strip=True)
                            url = link_element.get('href')
                            book_links.append((url, title))
                
                print(f"Found {len(page_articles)} articles on page {i+1}")
                
            except Exception as e:
                print(f"Error processing pagination page {page_url}: {e}")
        
        # Remove duplicate book links
        unique_book_links = []
        seen_urls = set()
        for url, title in book_links:
            if url not in seen_urls:
                unique_book_links.append((url, title))
                seen_urls.add(url)
        
        print(f"\nTotal unique books found: {len(unique_book_links)}")
        
        # Process individual book pages
        for i, (book_url, book_title) in enumerate(unique_book_links, 1):
            print(f"\n[{i}/{len(unique_book_links)}] Processing book: {book_title}")
            
            try:
                # Visit book page
                driver.get(book_url)
                
                # Wait for content to load
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "entry-content"))
                    )
                except TimeoutException:
                    print("Book page load timed out. Proceeding with what we have...")
                
                # Small delay to ensure page is fully rendered
                time.sleep(random.uniform(1, 3))
                
                # Get page content
                book_html = driver.page_source
                
                # Create safe filename
                safe_name = get_safe_filename(book_url, book_title)
                filename = f"{safe_name}.html"
                filepath = os.path.join(books_dir, filename)
                
                # Save book HTML
                save_html(book_html, filepath)
                print(f"Saved book: {filepath}")
                
                # Check for PDFs or downloadable content
                book_soup = BeautifulSoup(book_html, 'html.parser')
                download_links = []
                
                # Find PDF links - different patterns
                for link in book_soup.find_all('a', href=True):
                    href = link['href'].lower()
                    if href.endswith('.pdf') or 'download' in href or 'attachment' in href:
                        download_links.append((link['href'], link.get_text(strip=True)))
                
                if download_links:
                    downloads_dir = os.path.join(books_dir, f"{safe_name}_downloads")
                    os.makedirs(downloads_dir, exist_ok=True)
                    
                    for j, (dl_url, dl_text) in enumerate(download_links):
                        try:
                            # Convert to absolute URL if necessary
                            if not dl_url.startswith('http'):
                                dl_url = urljoin(book_url, dl_url)
                                
                            print(f"  Downloading: {dl_url}")
                            
                            # Use requests to download the file
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                                'Referer': book_url
                            }
                            
                            response = requests.get(dl_url, headers=headers, stream=True)
                            response.raise_for_status()
                            
                            # Determine filename
                            dl_filename = os.path.basename(urlparse(dl_url).path)
                            if not dl_filename or len(dl_filename) < 5:
                                ext = '.pdf' if '.pdf' in dl_url.lower() else '.bin'
                                dl_filename = f"{safe_name}_download_{j+1}{ext}"
                            
                            dl_path = os.path.join(downloads_dir, dl_filename)
                            
                            # Save the file
                            with open(dl_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                            
                            print(f"  Saved: {dl_filename}")
                            
                        except Exception as e:
                            print(f"  Error downloading {dl_url}: {e}")
                
            except Exception as e:
                print(f"Error processing book {book_title}: {e}")
            
            # Add a random delay between book processing
            if i < len(unique_book_links):
                delay = random.uniform(3, 7)
                print(f"Waiting {delay:.1f} seconds before next book...")
                time.sleep(delay)
        
        print("\nScraping completed successfully!")
        
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
    
    finally:
        # Always close the driver
        driver.quit()
        print("Browser closed. Script finished.")

if __name__ == "__main__":
    scrape_with_selenium()