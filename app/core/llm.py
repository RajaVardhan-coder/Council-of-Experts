# app/core/llm.py
import os
from google import genai
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
