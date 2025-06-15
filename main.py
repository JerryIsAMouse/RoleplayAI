import os
import asyncio
import httpx

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
print("API key loaded:", OPENROUTER_API_KEY is not None)

if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY not set.")
    exit(1)

async def main():
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Say hello"}],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        print("HTTP status:", response.status_code)
        print("Response text:", response.text)

        if response.status_code != 200:
            print("❌ API error")
            return

        data = response.json()
        print("Full response:", data)

        try:
            print("AI:", data["choices"][0]["message"]["content"])
        except Exception as e:
            print("❌ Parsing error:", e)

if __name__ == "__main__":
    asyncio.run(main())
