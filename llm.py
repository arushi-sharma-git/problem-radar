import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def summarize(text, max_retries=3):
    return generate("Summarize this in one sentence: " + text[:1000], max_retries=max_retries)


def generate(prompt, max_retries=3):
    """Generic Gemini call for any prompt (used by cluster.py for cluster tagging,
    and reusable for insight extraction / idea generation prompts later)."""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            # 429 RESOURCE_EXHAUSTED = quota gone (per-minute or per-day).
            # Retrying burns more of the same limited quota for no benefit,
            # so fail fast instead of hammering it.
            if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                print(f"Quota exhausted, not retrying: {e}")
                raise
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 15)  # 1s, 2s, 4s (capped at 15s) — only for transient 503s
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise