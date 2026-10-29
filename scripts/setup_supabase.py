
import os
from dotenv import load_dotenv
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
print(f"Supabase URL: {url}")
if not url or not key:
    print("Missing keys - SQL file ready at supabase/migrations/001_initial_schema.sql")
    print("Run docker-compose up postgres for local")
else:
    print("Copy SQL from supabase/migrations/001_initial_schema.sql into Supabase Dashboard > SQL Editor")
