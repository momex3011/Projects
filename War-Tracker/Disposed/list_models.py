import google.generativeai as genai
import os

API_KEY = "AIzaSyBO5dHsp53nOKeeEWLZ51V0KBJz4Jvq9rM"
genai.configure(api_key=API_KEY)

print("--- AVAILABLE MODELS ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Name: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
