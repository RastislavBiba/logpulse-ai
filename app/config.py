import os
import logging
from google import genai
from google.genai.errors import APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notix-copilot")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

PREFERRED_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

def query_gemini(prompt: str) -> tuple[str, str]:
    """Vykoná dopyt na Gemini s automatickým prepínaním na záložný model pri chybe."""
    if not client:
        raise RuntimeError("GEMINI_API_KEY nie je nakonfigurovaný.")

    last_error = None
    for model_name in PREFERRED_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                return response.text, model_name
        except APIError as e:
            logger.warning(f"Model {model_name} zlyhal ({e.code}): {e.message}")
            last_error = e
            continue
        except Exception as e:
            logger.warning(f"Chyba pri modeli {model_name}: {e}")
            last_error = e
            continue

    raise RuntimeError(f"Všetky modely Gemini zlyhali. Posledná chyba: {last_error}")
