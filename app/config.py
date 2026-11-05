import os
import time
import logging
from google import genai
from google.genai.errors import APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notix-copilot")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

PREFERRED_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
]


def query_gemini(prompt: str) -> tuple[str, str, int, int, float]:
    """
    Vykoná dopyt na Gemini s fallbackom a zbiera LLMOps metriky:
    Vráti: (text_odpovede, pouzity_model, prompt_tokens, output_tokens, latency_seconds)
    """
    if not client:
        raise RuntimeError("GEMINI_API_KEY nie je nakonfigurovaný.")

    last_error = None
    start_time = time.perf_counter()

    for model_name in PREFERRED_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                latency = round(time.perf_counter() - start_time, 3)

                # Získanie tokenov z metadát odpovede
                prompt_tokens = 0
                output_tokens = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                    output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

                return response.text, model_name, prompt_tokens, output_tokens, latency

        except APIError as e:
            logger.warning(f"Model {model_name} zlyhal ({e.code}): {e.message}")
            last_error = e
            continue
        except Exception as e:
            logger.warning(f"Chyba pri modeli {model_name}: {e}")
            last_error = e
            continue

    raise RuntimeError(f"Všetky modely Gemini zlyhali. Posledná chyba: {last_error}")
