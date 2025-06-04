import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def download_article_pdfs():
    # Create directory for saving PDFs
    pdf_dir = 'article_pdfs'
    os.makedirs(pdf_dir, exist_ok=True)
    
    # User agent header for requests
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Directory containing HTML article files
    html_dir = "article_html_files"
    
    # Check if directory exists
    if not os.path.exists(html_dir):
        print(f"Error: Directory '{html_dir}' not found.")
        return
        
    # Get list of HTML files
    html_files = [f for f in os.listdir(html_dir) if f.endswith('.html')]
    
    print(f"Found {len(html_files)} HTML files to process")
    
    # Track success and failures
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    # Process each HTML file
    for i, html_file in enumerate(html_files, 1):
        try:
            file_path = os.path.join(html_dir, html_file)
            print(f"[{i}/{len(html_files)}] Processing: {html_file}")
            
            # Read the HTML file
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find PDF download link
            pdf_link = None
            
            # Method 1: Look for download link with id="pdf-download"
            pdf_element = soup.find('a', id='pdf-download')
            if pdf_element and pdf_element.get('href'):
                pdf_link = pdf_element.get('href')
            
            # Method 2: Look for input with PDF link
            if not pdf_link:
                pdf_input = soup.find('input', {'id': 'p_d', 'class': 'p_d'})
                if pdf_input and pdf_input.get('value'):
                    pdf_link = pdf_input.get('value')
            
            # Method 3: Look for any link ending with .pdf
            if not pdf_link:
                pdf_links = soup.find_all('a', href=lambda href: href and href.lower().endswith('.pdf'))
                if pdf_links:
                    pdf_link = pdf_links[0].get('href')
            
            # Skip if no PDF link found
            if not pdf_link:
                print(f"  No PDF link found in {html_file}")
                skipped_count += 1
                continue
                
            # Download PDF
            try:
                print(f"  Downloading PDF from: {pdf_link}")
                
                # Create filename from original PDF link
                pdf_filename = os.path.basename(urlparse(pdf_link).path)
                
                # If filename is not valid, use HTML filename with .pdf extension
                if not pdf_filename or not pdf_filename.lower().endswith('.pdf'):
                    pdf_filename = os.path.splitext(html_file)[0] + '.pdf'
                
                # Save path for PDF
                pdf_path = os.path.join(pdf_dir, pdf_filename)
                
                # Check if PDF already exists
                if os.path.exists(pdf_path):
                    print(f"  PDF already exists: {pdf_filename}")
                    skipped_count += 1
                    continue
                
                # Download the PDF
                response = requests.get(pdf_link, headers=headers, stream=True)
                response.raise_for_status()
                
                # Save the PDF file
                with open(pdf_path, 'wb') as pdf_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            pdf_file.write(chunk)
                
                print(f"  Saved: {pdf_filename}")
                success_count += 1
                
                # Be polite to the server
                time.sleep(1)
                
            except Exception as e:
                print(f"  Error downloading PDF: {e}")
                failed_count += 1
                
        except Exception as e:
            print(f"Error processing {html_file}: {e}")
            failed_count += 1
    
    print(f"\nDownload Summary:")
    print(f"  Total files processed: {len(html_files)}")
    print(f"  Successfully downloaded: {success_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Skipped: {skipped_count}")

if __name__ == "__main__":
    download_article_pdfs()