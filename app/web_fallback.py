import os
from openai import OpenAI

def get_client():
    """Lazily initialize OpenAI client to allow test mocking."""
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def search_web_for_answer(question: str) -> str:
    """
    Search the web for an answer using OpenAI's web search via Responses API.
    Always prefixes the result as coming from the web, not the document.
    Falls back gracefully if web search is not available.
    """
    try:
        client = get_client()
        response = client.beta.chat.completions.create(
            model=os.getenv("CHAT_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "user",
                    "content": question
                }
            ],
            temperature=0,
            betas=["interleaved-thinking-20250514"]  # Enables web search capability
        )

        web_answer = response.choices[0].message.content.strip()
        return f"[From the web, not your document]: {web_answer}"
    except Exception as e:
        # Graceful fallback
        print(f"⚠ Web search unavailable: {e}")
        fallback = f"[General knowledge, unverified]: I don't have information in your document, but based on general knowledge, I can say: this would require additional research. Please verify important facts independently."
        return fallback
