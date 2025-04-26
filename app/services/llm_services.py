import google.generativeai as genai
from app.Config import Config

def configure_llm():
    genai.configure(api_key=Config.GEMINI_API_KEY)
    return genai.GenerativeModel('gemini-1.5-pro-latest')

def generate_content(model, prompt):
    response = model.generate_content(prompt)
    return response.text.strip()