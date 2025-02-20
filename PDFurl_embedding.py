import os
import requests
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, TextStringObject

pdf_urls = [
    "https://arxiv.org/pdf/1706.03762",
    "https://arxiv.org/pdf/1804.02767",
    "https://arxiv.org/pdf/2003.05656"
]

folder_name = "url_documents"
os.makedirs(folder_name, exist_ok=True)

def download_pdf(url, output_path):
    """Download PDF from URL and save it to the specified path."""
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded temporarily: {os.path.abspath(output_path)}")  # Print absolute path
    else:
        print(f"Failed to download {url}")

def embed_metadata(pdf_path, output_path, source_url):
    """Embed source URL into the metadata of a PDF."""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    metadata = reader.metadata or {}
    new_metadata = {NameObject(key): TextStringObject(str(value)) for key, value in metadata.items()}

    new_metadata[NameObject("/SourceURL")] = TextStringObject(source_url)

    writer.add_metadata(new_metadata)

    with open(output_path, "wb") as file:
        writer.write(file)

    print(f"Metadata added and saved in: {os.path.abspath(output_path)}")  #

def process_pdfs(pdf_urls):
    """Process multiple PDFs: download, embed metadata, and clean up."""
    for url in pdf_urls:
        # Extract filename from the URL (e.g., "1706.03762.pdf")
        filename = url.split("/")[-1] 
        temp_pdf_filename = f"{filename}.pdf" 
        pdf_with_metadata_filename = os.path.join(folder_name, f"{filename}.pdf")

        download_pdf(url, temp_pdf_filename)
        embed_metadata(temp_pdf_filename, pdf_with_metadata_filename, url)
        os.remove(temp_pdf_filename)  # Remove temporary file
        print(f"Temporary file removed: {temp_pdf_filename}")

# Run the process for all URLs
process_pdfs(pdf_urls)
