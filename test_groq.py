import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("Groq API key not found. Check your .env file.")

try:
    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": "Explain a database connection timeout and suggest three investigation steps."
            }
        ]
    )

    print("\nAI RESPONSE:\n")
    print(response.choices[0].message.content)

except Exception as error:
    print("Error:", error)