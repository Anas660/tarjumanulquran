import requests
import os
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def scrape_tarjumanulquran():
    # Create directories to store HTML files
    os.makedirs('pages', exist_ok=True)
    os.makedirs('articles', exist_ok=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    base_url = "https://www.tarjumanulquran.org/authors/2003/"
    
    def get_html(url):
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    
    def save_html(content, file_path):
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
    
    def get_safe_filename(url):
        # Create a filename based on the URL
        path = urlparse(url).path
        filename = os.path.basename(path)
        
        if not filename:
            filename = url.replace('https://', '').replace('http://', '')
            filename = ''.join(c if c.isalnum() else '_' for c in filename)
            filename = filename[:50]
        
        # Ensure filename is safe and has .html extension
        filename = ''.join(c if c.isalnum() or c in '._- ' else '_' for c in filename)
        if not filename.endswith('.html'):
            filename += '.html'
        
        return filename
    
    def extract_pagination_links(soup, url):
        print("Extracting pagination links...")
        pagination_urls = []
        
        # Look for pagination elements to determine the total number of pages
        pagination_elements = soup.select('.pagination a, .nav-links a, .page-numbers')
        
        # If not found with common classes, try finding any links with page numbers
        if not pagination_elements:
            links = soup.find_all('a')
            pagination_elements = [link for link in links if link.get('href') and 
                                  ('page' in link.get('href') or 'p=' in link.get('href'))]
        
        # Extract URLs from pagination elements
        highest_page_num = 1
        for element in pagination_elements:
            href = element.get('href')
            if href:
                full_url = urljoin(url, href)
                if full_url != url and full_url not in pagination_urls:
                    pagination_urls.append(full_url)
                    
                    # Try to extract the page number from the URL
                    try:
                        if 'page=' in href:
                            page_num = int(href.split('page=')[1].split('&')[0])
                            highest_page_num = max(highest_page_num, page_num)
                    except ValueError:
                        continue
        
        # Generate all pagination URLs based on the detected pattern
        # Use 105 as the total number of pages based on the information provided
        total_pages = max(105, highest_page_num)
        base_pagination_url = url.split('?')[0]
        if '?' in url:
            base_pagination_url = url.split('?')[0]
        else:
            base_pagination_url = url.rstrip('/')
        
        # Generate URLs for all pages
        for page_num in range(2, total_pages + 1):
            generated_url = f"{base_pagination_url}?page={page_num}"
            if generated_url not in pagination_urls:
                pagination_urls.append(generated_url)
        
        print(f"Found {len(pagination_urls)} pagination URLs")
        return sorted(pagination_urls, key=lambda x: int(x.split('page=')[1]) if 'page=' in x else 0)
    
    def extract_article_links(soup, page_url):
        print(f"Extracting article links from {page_url}...")
        article_urls = []
        
        # Method 1: Find article containers
        articles = soup.find_all('article')
        for article in articles:
            links = article.find_all('a')
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(page_url, href)
                    if full_url not in article_urls:
                        article_urls.append(full_url)
        
        # Method 2: Find headings with links (common for article titles)
        if not article_urls:
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
            for heading in headings:
                links = heading.find_all('a')
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(page_url, href)
                        if full_url not in article_urls:
                            article_urls.append(full_url)
        
        # Method 3: Look for common article containers
        if not article_urls:
            article_containers = soup.select('.post, .entry, .content, .article')
            for container in article_containers:
                links = container.find_all('a')
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(page_url, href)
                        if full_url not in article_urls and urlparse(full_url).netloc == urlparse(page_url).netloc:
                            article_urls.append(full_url)
        
        print(f"Found {len(article_urls)} article URLs")
        return article_urls
    
    def save_articles(article_urls, page_num):
        pdf_dir = os.path.join('articles', 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)
        
        for i, article_url in enumerate(article_urls, start=1):
            try:
                print(f"Downloading article {i} from page {page_num}: {article_url}")
                article_html = get_html(article_url)
                
                # Create filename for the HTML
                article_filename = f'page{page_num}_article{i}_{get_safe_filename(article_url)}'
                
                # Save article HTML
                save_html(article_html, os.path.join('articles', article_filename))
                
                # Check if there's a PDF link
                soup = BeautifulSoup(article_html, 'html.parser')
                
                # Find PDF download link - try multiple patterns
                pdf_link = None
                # Pattern 1: Look for PDF download link with ID
                pdf_a_tag = soup.find('a', id='pdf-download')
                if pdf_a_tag and pdf_a_tag.get('href'):
                    pdf_link = pdf_a_tag.get('href')
                
                # Pattern 2: Look for links containing PDF
                if not pdf_link:
                    pdf_links = soup.find_all('a', href=lambda href: href and '.pdf' in href)
                    if pdf_links:
                        pdf_link = pdf_links[0].get('href')
                
                # Pattern 3: Look for links with PDF images
                if not pdf_link:
                    img_pdf_elements = soup.find_all('img', class_='img-pdf')
                    for img in img_pdf_elements:
                        if img.parent and img.parent.name == 'a' and img.parent.get('href'):
                            pdf_link = img.parent.get('href')
                            break
                
                # Download PDF if found
                if pdf_link:
                    pdf_url = urljoin(article_url, pdf_link)
                    print(f"  Found PDF: {pdf_url}")
                    
                    try:
                        # Download the PDF
                        response = requests.get(pdf_url, headers=headers, stream=True)
                        response.raise_for_status()
                        
                        # Create PDF filename
                        pdf_filename = os.path.basename(pdf_url)
                        if not pdf_filename or not pdf_filename.lower().endswith('.pdf'):
                            pdf_filename = f'page{page_num}_article{i}_{get_safe_filename(article_url)}.pdf'
                        else:
                            # Prepend page and article number for organization
                            pdf_filename = f'page{page_num}_article{i}_{pdf_filename}'
                        
                        # Save the PDF file
                        pdf_filepath = os.path.join(pdf_dir, pdf_filename)
                        with open(pdf_filepath, 'wb') as pdf_file:
                            for chunk in response.iter_content(chunk_size=8192):
                                pdf_file.write(chunk)
                        
                        print(f"  PDF saved as: {pdf_filename}")
                    except Exception as pdf_error:
                        print(f"  Error downloading PDF: {pdf_error}")
                
                time.sleep(1)  # Be polite to the server
            except Exception as e:
                print(f"Error saving article {article_url}: {e}")
    
    # Main process
    try:
        print(f"Starting with base URL: {base_url}")
        
        # Get the first page
        main_page_html = get_html(base_url)
        
        # Save the first page
        first_page_filename = 'page_1.html'
        save_html(main_page_html, os.path.join('pages', first_page_filename))
        print(f"Saved page 1 as {first_page_filename}")
        
        # Parse the first page
        soup = BeautifulSoup(main_page_html, 'html.parser')
        
        # Extract article links from the first page
        article_links = extract_article_links(soup, base_url)
        save_articles(article_links, 1)
        
        # Extract pagination links
        page_urls = extract_pagination_links(soup, base_url)
        
        # Process each pagination page
        for i, page_url in enumerate(page_urls, start=2):
            try:
                print(f"Processing page {i}: {page_url}")
                page_html = get_html(page_url)
                page_filename = f'page_{i}.html'
                save_html(page_html, os.path.join('pages', page_filename))
                
                page_soup = BeautifulSoup(page_html, 'html.parser')
                page_article_links = extract_article_links(page_soup, page_url)
                save_articles(page_article_links, i)
                
                time.sleep(1)  # Prevent overloading the server
            except Exception as e:
                print(f"Error processing page {page_url}: {e}")
    
    except Exception as e:
        print(f"Error: {e}")
    
    print("Web scraping completed.")

if __name__ == "__main__":
    scrape_tarjumanulquran()