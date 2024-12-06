import os
import requests
from pymongo import MongoClient
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# MongoDB client setup
client = MongoClient('mongodb://localhost:27017/')  
db = client['ragbot_db']  

# Collections for Coin data and Financial data
collection1 = db['prodex_script.cryptoidentities']  # General Coin Info
collection2 = db['prodex_script.projectdetails']  # Project Details

# Function to get data from both collections (collection1 and collection2)
def get_coin_data(coin_id):
    try:
        # Fetch data from collection1 using coin_id
        coin_data = collection1.find_one({"_id": coin_id})
        
        if coin_data:
            # Fetch additional financial data from collection2 using coin's coinMarketCapId
            project_data = collection2.find_one({"projectId": coin_data["_id"]})
            
            # Combine data from both collections
            coin_data['project_data'] = project_data if project_data else {}
            return coin_data
        else:
            print(f"No data found for coin with ID: {coin_id}")
            return None
    except Exception as e:
        print(f"Error occurred while fetching data: {e}")
        return None

# Function to create a folder for the coin with project ID (instead of timestamp)
def create_coin_folder(coin_data):
    if coin_data:
        coin_name = coin_data.get("name")
        coin_id = str(coin_data.get("_id"))
        project_id = str(coin_data.get("project_data", {}).get("projectId", "Unknown"))
        
        # Use the projectId as a unique folder name
        folder_name = f"{coin_name}_{project_id}"
        folder_path = os.path.join('data', folder_name)  # Use coin_name + project_id for folder

        # Check if the folder already exists
        if os.path.exists(folder_path):
            print(f"Folder already exists for coin {coin_name} with project ID {project_id}: {folder_path}. Skipping folder creation.")
            return folder_path  # Return existing folder path without creating it
        else:
            # If the folder doesn't exist, create it
            os.makedirs(folder_path)
            print(f"Folder created for coin {coin_name} with ID {coin_id} and project ID {project_id}: {folder_path}")
            return folder_path
    else:
        print("No coin data to create a folder.")
        return None

# Function to download and save technical documents (PDFs) to the coin's folder
def download_technical_docs_for_coin(coin_data, folder_path):
    if coin_data:
        # Fetch the technical docs (assumed to be a list of URLs in the 'technicalDoc' field)
        technical_docs = coin_data.get('project_data', {}).get('technicalDoc', [])
        
        for doc_url in technical_docs:
            if doc_url.endswith(".pdf"):
                # Extract the filename from the URL
                filename = os.path.basename(doc_url)
                project_id = str(coin_data.get("project_data", {}).get("projectId", "Unknown"))

                # Create a new filename using project_id (e.g., 3256t7.pdf)
                new_filename = f"{project_id}_{filename}"
                file_path = os.path.join(folder_path, new_filename)

                # Check if the file already exists in the folder
                if os.path.exists(file_path):
                    print(f"File {new_filename} already exists in {folder_path}. Skipping download.")
                    continue
                
                # Download and save the PDF file
                try:
                    response = requests.get(doc_url, stream=True)
                    if response.status_code == 200:
                        with open(file_path, "wb") as file:
                            for chunk in response.iter_content(chunk_size=1024):
                                file.write(chunk)
                        print(f"Downloaded and saved {new_filename} to {folder_path}.")
                    else:
                        print(f"Failed to download {doc_url}. Status code: {response.status_code}")
                except Exception as e:
                    print(f"Error downloading {doc_url}: {e}")

# Fetch all coin IDs from collection1 and process each coin
def process_all_coins():
    try:
        # Get all coins from collection1
        coins = collection1.find()  # This fetches all coins

        # Loop through all coins and process them
        for coin in coins:
            coin_id = coin.get("_id")
            coin_data = get_coin_data(coin_id)  # Get the coin data using the coin_id

            if coin_data:
                print(f"Coin Data: {coin_data}")
                folder_path = create_coin_folder(coin_data)  # Create the folder for the coin
                if folder_path:
                    download_technical_docs_for_coin(coin_data, folder_path)  # Download and save PDFs in the folder
    
    except Exception as e:
        print(f"Error occurred while processing coins: {e}")

# Run the process to fetch all coins, create folders, and download technical docs (PDFs)
process_all_coins()

# logger.info("process_all_coins executed successfully!")
# print("process_all_coins executed successfully!")

