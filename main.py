import os
import asyncio
import httpx

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY not set in env variables.")
    exit(1)

async def main():
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",  # replace with your model name if different
        "messages": [
            {"role": "user", "content": "Say hello"}
        ]
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, headers=headers, json=payload)

        # Check status
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code} - {response.text}")
            return

        data = response.json()

        # Print entire response for debug
        print("Full response:", data)

        # Extract and print AI message
        try:
            ai_message = data["choices"][0]["message"]["content"]
            print("AI says:", ai_message)
        except (KeyError, IndexError):
            print("❌ Response JSON missing expected 'choices' key or content.")

if __name__ == "__main__":
    asyncio.run(main())
