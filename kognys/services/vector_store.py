# kognys/services/vector_store.py
import os, json
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from openai import OpenAI

_DB  = os.getenv("VECTOR_DB",  "kognys")
_COL = os.getenv("VECTOR_COL", "research_docs")
_OPENAI = OpenAI()

_client = MongoClient(os.environ["MONGODB_URI"], server_api=ServerApi("1"))
_vect_col = _client[_DB][_COL]

EMBED_MODEL = "text-embedding-3-small"

def embed(text: str) -> list[float]:
    res = _OPENAI.embeddings.create(input=[text], model=EMBED_MODEL)
    return res.data[0].embedding

def similarity_search(query: str, k: int = 4) -> list[dict]:
    query_vec = embed(query)
    pipeline = [
        {"$vectorSearch": {
            "index": "default",
            "path": "embedding",
            "queryVector": query_vec,
            "numCandidates": 100,
            "limit": k
        }},
        {"$project": {"_id": 0, "content": 1, "score": {"$meta": "vectorSearchScore"}}}
    ]
    return list(_vect_col.aggregate(pipeline))
