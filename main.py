import os
import asyncio
import httpx

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # Get from env
if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY not found in environment variables.")
    exit()

async def test_openrouter():
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://your-app.com",  # optional
        "X-Title": "TestBot",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",  # or gpt-3.5, etc.
        "messages": [{"role": "user", "content": "Say hello"}]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
        data = response.json()

        print("✅ OpenRouter response:", data["choices"][0]["message"]["content"])
    except Exception as e:
        print("❌ OpenRouter error:", e)

# Run it
asyncio.run(test_openrouter())
