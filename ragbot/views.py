# crypto_info/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import openai
from pymongo import MongoClient
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import OpenAI
import os
from dotenv import load_dotenv



# Load environment variables from .env file

load_dotenv()

# Set up OpenAI API keyask/ [name='ask']

openai.api_key = os.getenv('OPENAI_API_KEY')

# MongoDB setup

client = MongoClient('mongodb://localhost:27017/')
db = client['ragbot_db']
collection = db['prodex_script.cryptoidentities']
collection2 = db['prodex_script.cryptomarketdatas']  # Cryptomarket
collection3 = db['prodex_script.projectdetails']  # Project details

# Function to get data from all three collections
def get_coin_data(coin_name):
    # Fetch data from collection1
    coin_data = collection.find_one({"name": coin_name})
    
    if coin_data:
        # Fetch additional financial data from collection2 using coin's coinMarketCapId
        financial_data = collection2.find_one({"projectId": coin_data["_id"]})
        
        # Fetch project details from collection3 using coin's projectId
        project_data = collection3.find_one({"projectId": coin_data["_id"]})
        
        # Combine data from all collections
        coin_data['financial_data'] = financial_data if financial_data else {}
        coin_data['project_data'] = project_data if project_data else {}
        print(coin_data,"anuj")
        return coin_data
    
    else:
        return None


llm = OpenAI(temperature=0.3)

# Define the prompt template for generating a short answer
prompt_template = """
You are an AI assistant. Your task is to answer questions based solely on the information provided below and make it good reply. You are prohibited from using any external knowledge, assumptions, or completing any answer with information not explicitly included in the provided details. If the information necessary to answer the question is not available in the data, respond with: "The requested information is not available."


Coin Details:
Name: {name}
Symbol: {symbol}
Rank: {rank}
Coin Market: {coinMarketCapId}
First Historical Data: {firstHistoricalData}
Last Updated: {lastHistoricalData}
Platform Name: {platformName}
Token Address: {tokenAddress}
Created At:{createdAt}
Updated At:{updatedAt}

Financial Details:
Circulating Supply: {circulatingSupply}
Fully Diluted Market Cap USD:{fullyDilutedMarketCapUSD}
Market Cap By Total Supply USD:{marketCapByTotalSupplyUSD}
Market Cap Dominance:{marketCapDominance}
Market Cap USD: {marketCapUSD}
Max Supply:{maxSupply}
Num Market Pairs:{numMarketPairs}
Price USD: {priceUSD}
Volume (24h): {volume24hUSD}
Percent Change (1h):{percentChange1hUSD}
Percent Change (24h):{percentChange24hUSD}
Percent Change (30h):{percentChange30dUSD}
Percent Change (60h):{percentChange60dUSD}
Percent Change (7d):{percentChange7dUSD}
Percent Change (90d):{percentChange90dUSD}
Quote Last Updated:{quoteLastUpdated}
Self Reported Circulating Supply:{selfReportedCirculatingSupply}
Self Reported Market Cap:{selfReportedMarketCap}
Total Supply:{totalSupply}
Tvl Ratio:{tvlRatio}

Project Details:
Description: {description}
Explorer: {explorer}
Facebook:{facebook}
Source code: {sourceCode}
Message Board:{messageBoard}
Technical Doc:{technicalDoc}
Website:{website}

Question: {user_query}

Answer the question based strictly on the information above. If the question asks for a specific attribute (like rank, symbol, Project Name, or other details), return only that attribute as it appears in the data. Do not provide additional context or explanation not included in the details.

"""


# Initialize LangChain prompt
prompt = PromptTemplate(input_variables=["name", "symbol", "rank", "platformName", 
                                         "tokenAddress", "firstHistoricalData", "coinMarketCapId",
                                           "lastHistoricalData","updatedAt","createdAt" ,"circulatingSupply", 
                                           "marketCapUSD","fullyDilutedMarketCapUSD","marketCapByTotalSupplyUSD","marketCapDominance",
                                           "marketCapUSD","maxSupply","numMarketPairs","priceUSD","volume24hUSD","percentChange1hUSD",
                                           "percentChange24hUSD","percentChange30dUSD",
                                           "percentChange60dUSD","percentChange7dUSD","percentChange90dUSD","quoteLastUpdated",
                                           "selfReportedCirculatingSupply","selfReportedMarketCap","totalSupply","tvlRatio",
                                           "description", "explorer","facebook","messageBoard","technicalDoc","website",
                                           "sourceCode", "user_query"], template=prompt_template)


# Chain for generating the response using LangChain
chain = LLMChain(llm=llm, prompt=prompt)

def generate_coin_info_response(coin_name, user_query):
    coin_data = get_coin_data(coin_name)  # Get data from MongoDB
    
    if coin_data:
        # Check if financial data and project data exists in the coin document
        financial_data = coin_data.get('financial_data', {})
        project_data = coin_data.get('project_data', {})
        
        # Use LangChain to generate the response based on coin data and the user query
        response = chain.run(
            name=coin_data['name'],
            symbol=coin_data['symbol'],
            rank=coin_data['rank'],
            coinMarketCapId=coin_data['coinMarketCapId'],
            firstHistoricalData=coin_data['firstHistoricalData'],
            lastHistoricalData=coin_data['lastHistoricalData'],
            createdAt=coin_data['createdAt'],
            updatedAt=coin_data['updatedAt'],
            platformName=coin_data.get('platformName', 'N/A'),
            tokenAddress=coin_data.get('tokenAddress', 'N/A'),
            user_query=user_query,
            circulatingSupply=financial_data.get('circulatingSupply', 'N/A'),
            marketCapUSD=financial_data.get('marketCapUSD', 'N/A'),
            priceUSD=financial_data.get('priceUSD', 'N/A'),
            volume24hUSD=financial_data.get('volume24hUSD', 'N/A'),
            percentChange24hUSD=financial_data.get('percentChange24hUSD', 'N/A'),
            percentChange30dUSD=financial_data.get('percentChange30dUSD', 'N/A'),
            fullyDilutedMarketCapUSD=financial_data.get('fullyDilutedMarketCapUSD'),
            marketCapByTotalSupplyUSD=financial_data.get('marketCapByTotalSupplyUSD'),
            marketCapDominance=financial_data.get('marketCapByTotalSupplyUSD'),
            # marketCapUSD=financial_data.get('marketCapUSD'),
            maxSupply=financial_data.get('maxSupply'),
            numMarketPairs=financial_data.get('numMarketPairs'),
            # priceUSD=financial_data.get('priceUSD'),
            # volume24hUSD=financial_data.get('volume24hUSD'),
            percentChange1hUSD=financial_data.get('percentChange1hUSD'),
            # percentChange24hUSD=financial_data.get('percentChange24hUSD'),
            # percentChange30dUSD=financial_data.get('percentChange30dUSD'),
            percentChange60dUSD=financial_data.get('percentChange60dUSD'),
            percentChange7dUSD=financial_data.get('percentChange7dUSD'),
            percentChange90dUSD=financial_data.get('percentChange90dUSD'),
            quoteLastUpdated=financial_data.get('quoteLastUpdated'),
            selfReportedCirculatingSupply=financial_data.get('selfReportedCirculatingSupply'),
            selfReportedMarketCap=financial_data.get('selfReportedMarketCap'),
            totalSupply=financial_data.get('selfReportedMarketCap'),
            tvlRatio=financial_data.get('tvlRatio'),
            description=project_data.get('description', 'N/A'),
            explorer=project_data.get('explorer', 'N/A'),
            sourceCode=project_data.get('sourceCode', 'N/A'),
            facebook=project_data.get('facebook',   'N/A'),
            messageBoard=project_data.get('messageBoard'),
            technicalDoc=project_data.get('technicalDoc'),
            website=project_data.get('website'),
        )
        return response
    else:
        return f"No data found for{coin_name}. "

def extract_coin_name_from_query(user_query):
    try:
        prompt = f"Extract the name of the cryptocurrency mentioned in the following query: '{user_query}'"
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct", 
            prompt=prompt,
            max_tokens=20,
            n=1,
            stop=None,
            temperature=0.3
        )
        coin_name = response.choices[0].text.strip()
        print(coin_name)
        return coin_name
    except Exception as e:
        return f"Error extracting coin name: {str(e)}"


def classify_query(user_query):
    user_query_lower = user_query.lower()

    if "rank" in user_query_lower:
        if "top" in user_query_lower:
            
            digits = ''.join(filter(str.isdigit, user_query_lower.split("top")[-1]))
            if digits:
                top_n = int(digits)
                return "top_n_rank", {"n": top_n}
            else:
                return "invalid", None 

        else:
            
            digits = ''.join(filter(str.isdigit, user_query_lower))
            if digits:
                rank_m = int(digits)
                return "specific_rank", {"rank": rank_m}
            else:
                return "rank_query", None  

    return "general", None

# Function to get the top N ranked coins
def get_top_n_ranked_coins(n):
    return list(collection.find().sort("rank", 1).limit(n))

# Function to get a coin by specific rank
def get_coin_with_specific_rank(rank):
    return collection.find_one({"rank": rank})


import requests
@csrf_exempt  # Allow CSRF exemptions for POST requests
def handle_user_query(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print(data)
        user_query = data.get('user_query', '')
        
        print(user_query)
        if user_query:
            # Classify the query into a type and parameters
            query_type, params = classify_query(user_query)

            if query_type == "top_n_rank":
                # Handle top N ranked coin query
                coins = get_top_n_ranked_coins(params['n'])
                if coins:
                    top_n = "\n".join([f"{i+1}. {coin['name']} ({coin['symbol']}) - Rank {coin['rank']}" for i, coin in enumerate(coins)])
                    return JsonResponse({'response': f"The top {params['n']} ranked coins are:\n{top_n}"})

                return JsonResponse({'response': f"No data found for the top {params['n']} ranked coins."})

            elif query_type == "specific_rank":
                # Handle specific rank coin query
                coin = get_coin_with_specific_rank(params['rank'])
                if coin:
                    return JsonResponse({'response': f"The coin with rank {params['rank']} is {coin['name']} ({coin['symbol']})."})
                else:
                    return JsonResponse({'response': f"No coin found with rank {params['rank']}."})

            else:
                # General fallback query, such as requesting information about a specific coin
                coin_name = extract_coin_name_from_query(user_query)
                if coin_name:
                    coin_info = generate_coin_info_response(coin_name, user_query)
                    
                    if not coin_info or "No data found" in coin_info:
                        ragbot_app = "http://127.0.0.1:8000/api/ask-question/"  
    
                        try:
                            # Send query_text to the other API 
                            ragbot_app_response = requests.post(
                                ragbot_app,
                                json={"question": user_query}  # Use "query" as the field name instead of "query_text"
                            )

                            # Parse and print the response from the other backend
                            ragbot_app_response_data = ragbot_app_response.json()
                            print("Response from other backend:", ragbot_app_response_data)
                            
                            if 'answer' in ragbot_app_response_data:
                                return JsonResponse({'response': ragbot_app_response_data['answer']})
                            else:
                                return JsonResponse({'response': "External API did not return a valid response."})

                        except Exception as e:
                            print(f"Error calling external API: {str(e)}")
                            return JsonResponse({'response': "An error occurred while calling the external API. Please try again later."})
                    else:
                        return JsonResponse({'response': coin_info})
                else:
                    return JsonResponse({'response': "I'm sorry, I couldn't process your query. Please try again."})

        else:
            return JsonResponse({'response': 'No query provided.'}, status=400)

    return JsonResponse({'response': 'Invalid request method. Use POST.'}, status=405)