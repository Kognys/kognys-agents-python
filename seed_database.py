# seed_database.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_openai import OpenAIEmbeddings

# --- Configuration ---
load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("VECTOR_DB", "kognys")
COLLECTION_NAME = os.getenv("VECTOR_COL", "research_docs")

# --- Sample Documents ---
# We'll add some documents relevant to the test question
documents = [
    {
        "source": "TechCrunch 2023",
        "content": "Solid-state batteries are emerging as a promising alternative to traditional lithium-ion batteries, offering higher energy density and improved safety.",
    },
    {
        "source": "Science Daily 2024",
        "content": "Researchers have developed a new silicon anode technology that could dramatically increase the charging speed of electric vehicle batteries.",
    },
    {
        "source": "Industry Journal Q1 2023",
        "content": "Sodium-ion batteries are being explored as a lower-cost alternative for electric vehicles, especially for markets sensitive to the price of lithium.",
    },
]

def seed():
    """Connects to the DB, generates embeddings, and inserts documents."""
    print("🌱 Starting database seeding process...")

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Ensure the collection is empty before seeding to avoid duplicates
    if collection.count_documents({}) > 0:
        print("⚠️ Database already contains documents. Deleting existing documents.")
        collection.delete_many({})

    # Use the same embedding model as your retriever for consistency
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

    # Generate embeddings and add them to each document
    for doc in documents:
        doc["embedding"] = embedding_model.embed_query(doc["content"])
        print(f"  - Embedding and preparing doc from '{doc['source']}'")

    # Insert all documents into the collection
    collection.insert_many(documents)
    print(f"\n✅ Successfully inserted {len(documents)} documents into '{DB_NAME}.{COLLECTION_NAME}'.")
    client.close()

if __name__ == "__main__":
    if not all([MONGO_URI, DB_NAME, COLLECTION_NAME]):
        print("❌ Missing required environment variables in .env file.")
    else:
        seed()
