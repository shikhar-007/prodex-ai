import os
import time
from PyPDF2 import PdfReader
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import openai

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            if page.extract_text():  # Avoid empty pages
                text += page.extract_text()
        return text if text.strip() else None  # Return None for completely empty PDFs
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return None

# Split text into chunks
def split_text(text, chunk_size=1000):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=100)
    return text_splitter.split_text(text)

# Function to handle retries on rate limit error
def handle_rate_limit_error(func, *args, **kwargs):
    retries = 5  # Number of retry attempts
    backoff_time = 2  # Initial backoff time in seconds
    for i in range(retries):
        try:
            return func(*args, **kwargs)
        except openai.error.RateLimitError as e:
            print(f"Rate limit error encountered. Retrying in {backoff_time} seconds...")
            time.sleep(backoff_time)  # Wait before retrying
            backoff_time *= 2  # Exponential backoff
    raise Exception("Exceeded maximum retry attempts due to rate limit errors.")

# Store texts in Chroma DB
def store_text_in_chromadb(text_list, ids_list, persist_directory="db", max_batch_size=5461):
    embeddings = OpenAIEmbeddings(openai_api_key="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")
    vector_store = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    
    # Prepare metadata as a list of dictionaries (or None)
    metadata_list = [None] * len(text_list)  # You can customize the metadata if needed
    
    # Add texts in smaller batches
    for i in range(0, len(text_list), max_batch_size):
        batch_texts = text_list[i:i + max_batch_size]
        batch_ids = ids_list[i:i + max_batch_size]
        batch_metadatas = metadata_list[i:i + max_batch_size]
        
        # Add this batch to Chroma DB
        handle_rate_limit_error(vector_store.add_texts, texts=batch_texts, ids=batch_ids, metadatas=batch_metadatas)
        
        print(f"Processed batch {i // max_batch_size + 1} of size {len(batch_texts)}.")
    
    vector_store.persist()
    print("Embeddings stored in ChromaDB.")
    return vector_store

# Main function to process PDFs
def process_and_store_pdfs(pdf_directory):
    embeddings = OpenAIEmbeddings(openai_api_key="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")
    vector_store = Chroma(persist_directory="db", embedding_function=embeddings)

    all_texts = []
    all_ids = []

    for root, _, files in os.walk(pdf_directory):
        for file_name in files:
            if file_name.endswith(".pdf"):
                pdf_path = os.path.join(root, file_name)
                print(f"Processing {pdf_path}...")
                text = extract_text_from_pdf(pdf_path)
                if text:
                    # Split the text into chunks
                    chunks = split_text(text)
                    
                    # Generate unique IDs for each chunk
                    base_name = os.path.splitext(file_name)[0]
                    for i, chunk in enumerate(chunks):
                        unique_id = f"{base_name}_chunk{i+1}"
                        all_texts.append(chunk)
                        all_ids.append(unique_id)

    if not all_texts or not all_ids:
        print("No valid PDFs found to store in ChromaDB.")
        return None

    # Add to ChromaDB with batch processing
    store_text_in_chromadb(all_texts, all_ids)
    print("Embeddings successfully stored.")
    return vector_store

# Run the script
def main():
    pdf_directory = "data/"  # Path to your PDFs
    process_and_store_pdfs(pdf_directory)

if __name__ == "__main__":
    main()
