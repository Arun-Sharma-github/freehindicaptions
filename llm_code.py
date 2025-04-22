import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()


# Retrieve environment variables
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

# DeepInfra API endpoint for chat completions
ENDPOINT = "https://api.deepinfra.com/v1/openai/chat/completions"

def generate_text(prompt, max_tokens=100, temperature=0.1, top_p=0.9):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPINFRA_API_KEY}"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "stream": False
    }
    
    try:
        response = requests.post(ENDPOINT, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an error for bad status codes
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"