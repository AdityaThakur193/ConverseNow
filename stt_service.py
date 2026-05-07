import os
import tempfile
from typing import Optional

import whisper

WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "base")
whisper_model = whisper.load_model(WHISPER_MODEL_NAME)

_NON_ENGLISH_PROMPTS = {
    "hi": "यह हिंदी वाक्य है।",
    "te": "ఇది తెలుగు వాక్యం.",
    "ta": "இது தமிழ் வாக்கியம்.",
    "kn": "ಇದು ಕನ್ನಡ ವಾಕ್ಯ.",
    "ml": "ഇത് മലയാളം വാക്യം.",
    "bn": "এটি বাংলা বাক্য।",
    "mr": "हे मराठी वाक्य आहे.",
    "gu": "આ ગુજરાતી વાક્ય છે.",
    "pa": "ਇਹ ਪੰਜਾਬੀ ਵਾਕ ਹੈ।",
    "ur": "یہ اردو جملہ ہے۔",
}


def _get_decode_options(language: str) -> dict:
    is_english = language == "en"

    # Non-English speech benefits from slightly stronger decoding and softer filters.
    options = {
        "language": language,
        "task": "transcribe",
        "fp16": False,
        "verbose": False,
        "temperature": 0.0 if is_english else (0.0, 0.2, 0.4),
        "condition_on_previous_text": False,
        "no_speech_threshold": 0.5 if is_english else 0.6,
        "logprob_threshold": -0.8 if is_english else -1.2,
        "compression_ratio_threshold": 2.0,
    }

    if not is_english:
        options["beam_size"] = 5
        prompt = _NON_ENGLISH_PROMPTS.get(language)
        if prompt:
            options["initial_prompt"] = prompt

    return options


def transcribe_wav(wav_bytes: bytes, src_lang: str = "en-IN") -> Optional[str]:
    if not wav_bytes:
        print("Whisper STT: empty wav_bytes")
        return None

    language = src_lang.split("-")[0].lower()

    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(wav_bytes)
            temp_path = temp_audio.name

        print(f"Whisper STT temp file: {temp_path}, size={len(wav_bytes)} bytes")

        decode_options = _get_decode_options(language)
        result = whisper_model.transcribe(temp_path, **decode_options)

        segments = result.get("segments") or []
        if segments:
            no_speech_probs = [segment.get("no_speech_prob", 0.0) for segment in segments]
            avg_no_speech_prob = sum(no_speech_probs) / len(no_speech_probs)

            logprobs = [
                segment.get("avg_logprob")
                for segment in segments
                if segment.get("avg_logprob") is not None
            ]
            avg_logprob = (sum(logprobs) / len(logprobs)) if logprobs else 0.0

            no_speech_cutoff = 0.45 if language == "en" else 0.65
            if avg_no_speech_prob > no_speech_cutoff:
                print(
                    "Whisper STT dropped transcript due to high no_speech_prob: "
                    f"{avg_no_speech_prob:.3f}"
                )
                return None

            logprob_cutoff = -1.0 if language == "en" else -1.6
            if avg_logprob < logprob_cutoff:
                print(
                    "Whisper STT dropped transcript due to low confidence avg_logprob: "
                    f"{avg_logprob:.3f}"
                )
                return None

        text = result.get("text", "").strip()
        if not text:
            print("Whisper STT: no text returned")
            return None

        print(f"Whisper final transcript: {text}")
        return text

    except Exception as e:
        print(f"Whisper STT error: {e}")
        return None

    finally:
        try:
            if "temp_path" in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass