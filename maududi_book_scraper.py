import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_and_save_book_pages():
    # Create directory to store book HTML files
    book_dir = 'maududi_books_html'
    os.makedirs(book_dir, exist_ok=True)
    
    # User agent to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://readmaududi.com/'
    }
    
    # List to track processed book links
    processed_books = []
    
    # Function to extract and process books from a category page
    def process_category_page(url):
        print(f"Processing category page: {url}")
        
        try:
            # Fetch the category page
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all book entry titles
            book_elements = soup.find_all('h3', class_='entry-title')
            print(f"Found {len(book_elements)} book entries on this page")
            
            # Extract book links
            for book_elem in book_elements:
                link_elem = book_elem.find('a')
                if link_elem and 'href' in link_elem.attrs:
                    book_url = link_elem['href']
                    book_title = link_elem.get_text(strip=True)
                    
                    # Skip if already processed
                    if book_url in processed_books:
                        print(f"Already processed: {book_title}")
                        continue
                    
                    processed_books.append(book_url)
                    
                    # Download the book page
                    print(f"Downloading book: {book_title} from {book_url}")
                    try:
                        book_response = requests.get(book_url, headers=headers)
                        book_response.raise_for_status()
                        
                        # Create a safe filename from the book URL
                        book_filename = book_url.strip('/').split('/')[-1]
                        if not book_filename:
                            # Use the second-to-last segment if the last is empty
                            parts = book_url.strip('/').split('/')
                            if len(parts) >= 2:
                                book_filename = parts[-2]
                            else:
                                book_filename = f"book_{len(processed_books)}"
                        
                        book_filename = f"{book_filename}.html"
                        book_path = os.path.join(book_dir, book_filename)
                        
                        # Save the book HTML
                        with open(book_path, 'w', encoding='utf-8') as file:
                            file.write(book_response.text)
                        
                        print(f"Saved book HTML to {book_path}")
                        
                        # Be polite to the server
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"Error downloading book {book_url}: {e}")
            
            # Check for pagination - look for next page link
            next_page_link = None
            pagination = soup.find('div', class_='page-nav')
            if pagination:
                next_link = pagination.find('a', class_='last')
                if next_link and 'href' in next_link.attrs:
                    next_page_link = next_link['href']
            
            return next_page_link
            
        except Exception as e:
            print(f"Error processing category page {url}: {e}")
            return None
    
    # Start with the main category URL
    category_url = "https://readmaududi.com/category/books-syed-maududi/others-books-of-maududi/"
    
    # Process first page and any subsequent pages
    next_url = category_url
    while next_url:
        next_url = process_category_page(next_url)
    
    print(f"Completed! Saved {len(processed_books)} book HTML files")

if __name__ == "__main__":
    extract_and_save_book_pages()