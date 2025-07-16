# seed_database.py
import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_openai import OpenAIEmbeddings

# --- Configuration ---
load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("VECTOR_DB", "kognys")
COLLECTION_NAME = os.getenv("VECTOR_COL", "research_docs")
DATA_FILE_PATH = "data/research_data.json" # <-- Path to our new data file

def seed():
    """
    Connects to the DB, loads data from a JSON file, generates embeddings,
    and inserts the documents.
    """
    print("🌱 Starting database seeding process...")

    # 1. Load documents from the JSON file
    try:
        with open(DATA_FILE_PATH, 'r') as f:
            documents = json.load(f)
        print(f"📄 Found {len(documents)} documents in '{DATA_FILE_PATH}'.")
    except FileNotFoundError:
        print(f"❌ Error: Data file not found at '{DATA_FILE_PATH}'. Please create it.")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from '{DATA_FILE_PATH}'. Please check the file format.")
        return

    # 2. Connect to the database
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # 3. Clear the existing collection
    if collection.count_documents({}) > 0:
        print("⚠️ Database already contains documents. Clearing the collection...")
        collection.delete_many({})
        print("Collection cleared.")

    # 4. Generate embeddings and insert new documents
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

    for doc in documents:
        doc["embedding"] = embedding_model.embed_query(doc["content"])
        print(f"  - Embedding doc from '{doc['source']}'")

    collection.insert_many(documents)
    print(f"\n✅ Successfully inserted {len(documents)} new documents into '{DB_NAME}.{COLLECTION_NAME}'.")
    client.close()

if __name__ == "__main__":
    if not MONGO_URI:
        print("❌ Missing MONGODB_URI environment variable.")
    else:
        seed()
