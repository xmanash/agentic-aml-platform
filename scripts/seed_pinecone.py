
import os
from dotenv import load_dotenv
load_dotenv()
PINECONE_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not PINECONE_KEY:
    print("No Pinecone key, seeding local JSON")
    os.makedirs("data/vector_store", exist_ok=True)
    import json
    json.dump({"entities":[{"id":"Bad Actor LLC"}]}, open("data/vector_store/local_index.json","w"))
    exit()

from pinecone import Pinecone
from openai import OpenAI
pc = Pinecone(api_key=PINECONE_KEY)
oa = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

def embed(t):
    if oa:
        return oa.embeddings.create(model="text-embedding-3-small", input=t).data[0].embedding
    import hashlib
    h = int(hashlib.md5(t.encode()).hexdigest(),16) % 1000
    return [float(h)/1000]*1536

idx = pc.Index("aml-entities")
vectors = [{"id":f"ent-{i}","values":embed(n),"metadata":{"name":n}} for i,n in enumerate(["Bad Actor LLC","Offshore Holdings","Test Entity","John Smith"])]
idx.upsert(vectors=vectors)
print(f"Seeded {len(vectors)}")
