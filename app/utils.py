import os
from dotenv import load_dotenv

def load_env():
    """Loads environment variables from .env file"""
    load_dotenv()

    required_keys = ["OPENAI_API_KEY", "SUPABASE_KEY"]
    for key in required_keys:
        value = os.getenv(key)
        if not value or value == "disabled":
            raise ValueError(f"Missing required environment variable: {key}")
        os.environ[key] = value

    # Optional: Ignore Stripe if set to "disabled"
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "disabled")
    if stripe_key != "disabled":
        os.environ["STRIPE_SECRET_KEY"] = stripe_key
