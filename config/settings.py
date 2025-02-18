import os
from dotenv import load_dotenv

def load_env():
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    os.environ["STRIPE_SECRET_KEY"] = os.getenv("STRIPE_SECRET_KEY")
