import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path

# Load env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "rag_learning")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "rag_documents")
VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME", "rag_vector_index")

if not MONGODB_URI:
    print("Error: MONGODB_URI not found.")
    sys.exit(1)

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
collection = db[MONGODB_COLLECTION]

print(f"Checking collection: {MONGODB_DB}.{MONGODB_COLLECTION}")

try:
    indexes = list(collection.list_search_indexes())
    print(f"Found {len(indexes)} search indexes:")
    found = False
    for idx in indexes:
        print(f" - {idx.get('name')}")
        if idx.get("name") == VECTOR_INDEX_NAME:
            found = True
    
    if found:
        print(f"\n[SUCCESS] Vector Index '{VECTOR_INDEX_NAME}' exists!")
        
        # Also check if there is any data
        count = collection.count_documents({})
        print(f"Document count in collection: {count}")
    else:
        print(f"\n[FAILURE] Vector Index '{VECTOR_INDEX_NAME}' NOT found.")
        print("You must create it in MongoDB Atlas UI.")

except Exception as e:
    print(f"Error checking indexes (Atlas Search might not be enabled or connection issue): {e}")
