
import os
from dotenv import load_dotenv
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    print("PINECONE_API_KEY missing - using local FAISS fallback")
else:
    from pinecone import Pinecone, ServerlessSpec
    pc = Pinecone(api_key=PINECONE_API_KEY)
    indexes = {
        "aml-entities": 1536,
        "aml-cases": 1536,
        "aml-adverse-media": 1536,
        "aml-documents": 1536,
    }
    existing = [i['name'] for i in pc.list_indexes()]
    for name, dim in indexes.items():
        if name in existing:
            print(f"Exists {name}")
            continue
        print(f"Creating {name}")
        pc.create_index(name=name, dimension=dim, metric="cosine", spec=ServerlessSpec(cloud="aws", region="us-east-1"))
    print("All indexes ready")
