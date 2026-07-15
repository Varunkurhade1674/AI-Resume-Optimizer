import os
from openai import OpenAI

client = OpenAI(
    api_key="your_groq_api_key_here",
    base_url="https://openrouter.ai/api/v1"
)

try:
    response = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=[{"role": "user", "content": "hi"}]
    )
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
