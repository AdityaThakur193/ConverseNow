import os
from typing import Optional

from sarvamai import SarvamAI
from sarvamai.errors import ForbiddenError

_LANGUAGE_MAP = {
    "en": "en-IN",
    "en-in": "en-IN",
    "english": "en-IN",
    "hi": "hi-IN",
    "hi-in": "hi-IN",
    "hindi": "hi-IN",
    "te": "te-IN",
    "te-in": "te-IN",
    "telugu": "te-IN",
    "ta": "ta-IN",
    "ta-in": "ta-IN",
    "tamil": "ta-IN",
    "kn": "kn-IN",
    "kn-in": "kn-IN",
    "kannada": "kn-IN",
    "ml": "ml-IN",
    "ml-in": "ml-IN",
    "malayalam": "ml-IN",
    "bn": "bn-IN",
    "bn-in": "bn-IN",
    "bengali": "bn-IN",
    "mr": "mr-IN",
    "mr-in": "mr-IN",
    "marathi": "mr-IN",
    "gu": "gu-IN",
    "gu-in": "gu-IN",
    "gujarati": "gu-IN",
    "pa": "pa-IN",
    "pa-in": "pa-IN",
    "punjabi": "pa-IN",
    "ur": "ur-IN",
    "ur-in": "ur-IN",
    "urdu": "ur-IN",
}

_runtime_state = {
    "client": None,
    "api_key": None,
    "unavailable": False,
}


def _normalize_lang(code: str, fallback: str) -> str:
    if not code:
        return fallback
    normalized_code = code.strip().lower()
    return _LANGUAGE_MAP.get(normalized_code, fallback)


def _get_client() -> Optional[SarvamAI]:
    api_key = os.getenv("SARVAM_API_KEY", "").strip()
    if not api_key:
        print("Sarvam translation unavailable: missing SARVAM_API_KEY")
        _runtime_state["unavailable"] = True
        _runtime_state["client"] = None
        _runtime_state["api_key"] = None
        return None

    # If the key changed at runtime, force re-initialization with the new key.
    if _runtime_state["api_key"] != api_key:
        _runtime_state["client"] = None
        _runtime_state["api_key"] = api_key
        _runtime_state["unavailable"] = False

    if _runtime_state["unavailable"]:
        return None

    existing_client = _runtime_state["client"]
    if existing_client is not None:
        return existing_client

    try:
        client = SarvamAI(api_subscription_key=api_key)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Sarvam translation unavailable: {error}")
        _runtime_state["unavailable"] = True
        return None

    _runtime_state["client"] = client
    return client


def translate_text(text: str, src_lang: str, tgt_lang: str) -> Optional[str]:
    if not text:
        return text

    client = _get_client()
    if client is None:
        return text

    source_language_code = _normalize_lang(src_lang, "en-IN")
    target_language_code = _normalize_lang(tgt_lang, "hi-IN")

    if source_language_code == target_language_code:
        print(
            f"Sarvam translation skipped: source and target are the same ({source_language_code})"
        )
        return text

    try:
        response = client.text.translate(
            input=text,
            source_language_code=source_language_code,
            target_language_code=target_language_code,
            model="sarvam-translate:v1",
        )
        translated_text = (response.translated_text or "").strip()
        return translated_text if translated_text else text
    except ForbiddenError as error:
        print(f"Sarvam translation unavailable: {error}")
        _runtime_state["client"] = None
        _runtime_state["unavailable"] = True
        return text
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Sarvam translation error: {error}")
        return text