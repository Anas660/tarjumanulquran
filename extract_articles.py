import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

def extract_articles(html_file_path, headers=None):
    """Extract individual articles from HTML and save as text files."""
    
    # Create directory to store article files
    output_dir = 'articles_text'
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the HTML file
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # Parse HTML using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract the page number from the filename for organization
    page_num = os.path.basename(html_file_path).replace('page_', '').replace('.html', '')
    
    # Check if this page has embedded articles or just links
    article_divs = soup.find_all('div', class_='tab-pane', id=lambda x: x and x.startswith('v-pills-'))
    has_content = any(len(div.text.strip()) > 2 for div in article_divs)  # Check if divs have substantial content
    
    if has_content:
        # Process embedded articles (pages 1-20)
        return process_embedded_articles(soup, page_num, output_dir)
    else:
        # Process article links (pages 21+)
        return process_article_links(soup, page_num, output_dir, headers)

def process_embedded_articles(soup, page_num, output_dir):
    """Process articles embedded in the page."""
    # Find all article divs (tab-panes)
    article_divs = soup.find_all('div', class_='tab-pane', id=lambda x: x and x.startswith('v-pills-'))
    
    print(f"Found {len(article_divs)} embedded articles in page {page_num}")
    
    # Process each article
    count = 0
    for index, article_div in enumerate(article_divs, 1):
        # Get article ID
        article_id = article_div.get('id', '').replace('v-pills-', '')
        
        # Skip empty articles
        if len(article_div.text.strip()) <= 2:  # Skip articles with minimal content
            continue
            
        count += 1
        
        # Get article title
        title_tag = article_div.find('h2')
        title = title_tag.get_text(strip=True) if title_tag else f"Article {article_id}"
        
        # Extract full content with formatting
        content_parts = []
        
        # First add the title
        content_parts.append(title)
        content_parts.append("")  # Blank line after title
        
        # Process all headings, paragraphs, and lists
        for element in article_div.find_all(['h2', 'h3', 'h4', 'p', 'ul', 'ol', 'hr']):
            if element.name in ['h2', 'h3', 'h4']:
                # Skip the main title which we've already added
                if element == title_tag:
                    continue
                content_parts.append(element.get_text(strip=True))
                content_parts.append("")  # Blank line after heading
            elif element.name == 'p':
                content_parts.append(element.get_text(strip=True))
                content_parts.append("")  # Blank line after paragraph
            elif element.name == 'hr':
                content_parts.append("---------------------")
                content_parts.append("")
            elif element.name in ['ul', 'ol']:
                for li in element.find_all('li'):
                    content_parts.append(f"• {li.get_text(strip=True)}")
                content_parts.append("")  # Blank line after list
        
        # Combine content parts into full text
        full_text = "\n".join(content_parts)
        
        # Create safe filename
        safe_title = re.sub(r'[\\/*?:"<>|]', '', title)
        safe_title = safe_title[:50] if len(safe_title) > 50 else safe_title
        filename = f"page{page_num}_article{index}_{article_id}_{safe_title}.txt"
        filepath = os.path.join(output_dir, filename)
        
        # Save article to text file
        with open(filepath, 'w', encoding='utf-8') as out_file:
            out_file.write(full_text)
        
        print(f"Saved: {filename}")
    
    return count

def process_article_links(soup, page_num, output_dir, headers):
    """Extract and process links to individual article pages."""
    # Find all article links
    article_links = []
    link_containers = soup.find_all('div', style=lambda x: x and 'background-color: #6c8d9e' in x)
    
    print(f"Found {len(link_containers)} article links in page {page_num}")
    
    for index, container in enumerate(link_containers, 1):
        link = container.find('a')
        if not link:
            continue
            
        article_url = link['href']
        title_element = link.find('h4')
        title = title_element.get_text(strip=True) if title_element else f"Article {index}"
        
        # Find date and category if available
        date = ""
        category = ""
        span_elements = link.find_all('p1')
        if len(span_elements) >= 1:
            date = span_elements[0].get_text(strip=True)
        if len(span_elements) >= 2:
            category = span_elements[1].get_text(strip=True)
            
        article_links.append((article_url, title, date, category, index))
    
    # Fetch and save each article
    for article_url, title, date, category, index in article_links:
        try:
            print(f"Fetching article {index} from page {page_num}: {article_url}")
            
            # Request the article page
            if headers:
                response = requests.get(article_url, headers=headers)
            else:
                response = requests.get(article_url)
                
            response.raise_for_status()
            article_soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract article content
            article_content = article_soup.find('div', class_='article-content')
            if not article_content:
                article_content = article_soup.find('div', class_='entry-content')
            if not article_content:
                article_content = article_soup.find('div', class_='content')
            
            if not article_content:
                print(f"Warning: Could not find article content for {article_url}")
                continue
                
            # Extract full content with formatting
            content_parts = []
            
            # Add title and metadata
            content_parts.append(title)
            
            if date or category:
                metadata = []
                if date:
                    metadata.append(f"تاريخ: {date}")
                if category:
                    metadata.append(f"زمرہ: {category}")
                content_parts.append(" | ".join(metadata))
            
            content_parts.append("")  # Blank line
            content_parts.append("=" * 50)
            content_parts.append("")  # Blank line
            
            # Process all headings, paragraphs, and lists
            for element in article_content.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol', 'hr']):
                if element.name in ['h1', 'h2', 'h3', 'h4']:
                    content_parts.append(element.get_text(strip=True))
                    content_parts.append("")  # Blank line after heading
                elif element.name == 'p':
                    text = element.get_text(strip=True)
                    if text:  # Only add non-empty paragraphs
                        content_parts.append(text)
                        content_parts.append("")  # Blank line after paragraph
                elif element.name == 'hr':
                    content_parts.append("-" * 30)
                    content_parts.append("")
                elif element.name in ['ul', 'ol']:
                    for li in element.find_all('li'):
                        content_parts.append(f"• {li.get_text(strip=True)}")
                    content_parts.append("")  # Blank line after list
            
            # Combine content parts into full text
            full_text = "\n".join(content_parts)
            
            # Create safe filename from URL
            url_parts = article_url.split('/')
            url_slug = url_parts[-1] if url_parts[-1] else url_parts[-2]
            
            # Create filename with page number and slug
            filename = f"page{page_num}_article{index}_{url_slug}.txt"
            filepath = os.path.join(output_dir, filename)
            
            # Save article to text file
            with open(filepath, 'w', encoding='utf-8') as out_file:
                out_file.write(full_text)
            
            print(f"Saved: {filename}")
            
            # Be polite to the server
            time.sleep(1)
            
        except Exception as e:
            print(f"Error processing article {article_url}: {e}")
    
    return len(article_links)

def process_all_html_files(directory):
    """Process all HTML files in the given directory."""
    total_articles = 0
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Get all HTML files in the directory
    html_files = [f for f in os.listdir(directory) if f.endswith('.html') and f.startswith('page_')]
    
    for html_file in sorted(html_files, key=lambda x: int(x.replace('page_', '').replace('.html', ''))):
        file_path = os.path.join(directory, html_file)
        num_articles = extract_articles(file_path, headers)
        total_articles += num_articles
        print(f"Processed {html_file}: {num_articles} articles")
    
    print(f"Total articles extracted: {total_articles}")

# Path to your HTML files directory
html_dir = "d:\\pixelpk projects\\tarjumanulquran\\pages"


# Process all HTML files or a single file
process_all_html_files(html_dir)