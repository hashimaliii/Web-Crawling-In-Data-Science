import os
import time
import pandas as pd
import fitz
import json
from google import genai
from sentence_transformers import SentenceTransformer
import crawling_spider

def generate_label(text):
    """Generate a label using Gemini API with predefined categories."""
    categories = ["Deep Learning", "NLP", "Reinforcement Learning", "Computer Vision", "Optimization"]
    prompt = (
        f"Classify the following research paper into one of these categories: {', '.join(categories)}.\n\n"
        f"Paper Text: {text[:2000]}\n\n"  # Sending first 2000 characters to avoid excessive token usage
        f"Provide only the category name as output."
    )
    
    retries = 3
    for _ in range(retries):
        try:
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            label = response.text.strip()
            if label in categories:
                return label
            return "Uncategorized"
        except genai.errors.ClientError as e:
            if "RESOURCE_EXHAUSTED" in str(e):
                print("Quota exceeded. Retrying in 30 seconds...")
                time.sleep(30)
            else:
                return "Label generation failed"
    return "Label generation failed"

def clean_text(text):
    """Remove excessive line breaks and clean text."""
    return " ".join(text.split())

def process_pdf(pdf_path):
    """Process a PDF file to extract text, generate an embedding, and classify it."""
    pdf = fitz.open(pdf_path)
    text = "".join(page.get_text() for page in pdf)
    text = clean_text(text)  # Clean extracted text
    
    if not text.strip():  # Handle empty PDFs
        return {"filename": pdf_path, "label": "Unknown", "text": "", "embedding": None}
    
    embedding = model.encode(text).tolist()
    label = generate_label(text)
    
    return {"filename": pdf_path, "label": label, "text": text, "embedding": embedding}

def process_directory(directory_path):
    """Recursively process all PDFs in the directory and subdirectories."""
    data = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                print(f"Processing: {pdf_path}")  # Debugging print
                result = process_pdf(pdf_path)
                data.append(result)
    return data

if __name__ == "__main__":
    process = crawling_spider.CrawlerProcess()
    process.crawl(crawling_spider.PapersSpider)
    process.start()

    # Gemini QuickStart
    client = genai.Client(api_key="AIzaSyC7xaHYj8wPS5MWDnRhQ34kHvPMShlExMg")

    # Load the model for embeddings
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Folder path containing PDFs (fixed path issue)
    folder_path = r"papers"

    # Process all PDFs in the folder and subfolders
    pdf_data = process_directory(folder_path)

    # Store data in DataFrame and save to CSV with JSON-safe formatting
    df = pd.DataFrame(pdf_data)
    df['embedding'] = df['embedding'].apply(lambda x: json.dumps(x) if x is not None else None)
    df.to_csv("pdf_data.csv", index=False)
    print("Processing complete. Data saved to pdf_data_fixed.csv.")