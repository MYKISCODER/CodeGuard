import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

def main():
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )
    model = os.getenv("MODEL", "gpt-4o")

    try:
        resp = client.responses.create(
            model=model,
            instructions="You are a helpful assistant.",
            input="Reply with exactly: OK",
        )
        print("Responses OK:", resp.output_text.strip())
        return
    except Exception as e:
        print("Responses failed, fallback to chat.completions. Error:", type(e).__name__, e)

    comp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Reply with exactly: OK"},
        ],
    )
    print("ChatCompletions OK:", comp.choices[0].message.content.strip())

if __name__ == "__main__":
    main()
