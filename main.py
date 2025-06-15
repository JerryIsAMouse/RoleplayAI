import asyncio
import httpx

# Replace with your actual key (keep it secret!)
OPENROUTER_API_KEY = "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"

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
