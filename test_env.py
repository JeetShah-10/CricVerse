import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("SUPABASE_URL:", os.getenv('SUPABASE_URL'))
print("SUPABASE_ANON_KEY:", os.getenv('SUPABASE_ANON_KEY'))
print("SUPABASE_KEY:", os.getenv('SUPABASE_KEY'))
print("DATABASE_URL:", os.getenv('DATABASE_URL'))