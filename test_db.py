import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fetch database credentials
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")  # Must be 'aws-0-eu-west-2.pooler.supabase.com'
DB_PORT = os.getenv("DB_PORT")  # Must be '6543'
DB_NAME = os.getenv("DB_NAME")

# Connect to Supabase Database
try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()

    print("✅ Database connection successful!")
    print(f"📅 Current Time from DB: {result}")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
