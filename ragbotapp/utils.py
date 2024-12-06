import os
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
import openai

# Load the OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key is not set in the environment variable.")

# Load ChromaDB with embeddings
def load_chromadb(persist_directory="../db"):
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vector_store = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    return vector_store

# Fallback mechanism: Query OpenAI GPT directly
def query_openai_gpt(prompt, model="gpt-4", max_tokens=200):
    try:
        openai.api_key = OPENAI_API_KEY
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error while querying GPT: {e}"

# Create RetrievalQA chain with fallback
def create_retrieval_qa_chain(vector_store):
    llm = ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY)
    retriever = vector_store.as_retriever()

    def run_with_custom_handling(question):
        # Attempt retrieval
        docs = retriever.get_relevant_documents(question)
        if not docs:
            # Fallback to GPT if no documents are found
            print("No relevant documents found. Falling back to OpenAI GPT...")
            return query_openai_gpt(question)
        else:
            # Use RetrievalQA if documents are found
            qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever)
            try:
                return qa_chain.run(question)
            except Exception as e:
                # Fallback in case RetrievalQA fails
                print("RetrievalQA chain failed. Falling back to OpenAI GPT...")
                return query_openai_gpt(question)

    return run_with_custom_handling
