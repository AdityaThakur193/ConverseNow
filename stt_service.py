import os
import tempfile
from typing import Optional

import whisper

WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "small")
print(f"Loading Whisper model: {WHISPER_MODEL_NAME}")
whisper_model = whisper.load_model(WHISPER_MODEL_NAME)

_NON_ENGLISH_PROMPTS = {
    "hi": "नमस्ते। यह हिंदी वाक्य है। कृपया सुनें। धन्यवाद।",
    "te": "నమస్కారం. ఇది తెలుగు వాక్యం. దయచేసి విను. ధన్యవాదాలు.",
    "ta": "வணக்கம். இது தமிழ் வாக்கியம். தயவுசெய்து கேளுங்கள். நன்றி.",
    "kn": "ನಮಸ್ಕಾರ. ಇದು ಕನ್ನಡ ವಾಕ್ಯ. ದಯವಿಟ್ಟು ಆಲಿಸಿ. ಧನ್ಯವಾದಗಳು.",
    "ml": "ഹലോ. ഇത് മലയാളം വാക്യം. കേൾക്കുക. നന്ദി.",
    "bn": "নমস্কার। এটি বাংলা বাক்য। দয়া করে শুনুন। ধন্যবাদ।",
    "mr": "नमस्कार. हे मराठी वाक्य आहे. कृपया ऐका. धन्यवाद.",
    "gu": "નમસ્તે. આ ગુજરાતી વાક્ય છે. કૃપયા સાંભળો. ધન્યવાદ.",
    "pa": "ਨਮਸ਼ਕਾਰ. ਇਹ ਪੰਜਾਬੀ ਵਾਕ ਹੈ. ਕਿਰਪਾ ਕਰਕੇ ਸੁਣੋ. ਧੰਨਵਾਦ.",
    "ur": "السلام علیکم. یہ اردو جملہ ہے. براہ کرم سنیں. شکریہ.",
}


def _validate_indic_text(text: str, language: str) -> bool:
    """Validate that the text contains valid Indic script characters and not garbled output."""
    if not text or not text.strip():
        return False

    # Unicode ranges for Indic scripts
    indic_ranges = {
        "hi": (0x0900, 0x097F),  # Devanagari
        "mr": (0x0900, 0x097F),  # Marathi (Devanagari)
        "te": (0x0C00, 0x0C7F),  # Telugu
        "ta": (0x0B80, 0x0BFF),  # Tamil
        "kn": (0x0C80, 0x0CFF),  # Kannada
        "ml": (0x0D00, 0x0D7F),  # Malayalam
        "bn": (0x0980, 0x09FF),  # Bengali
        "gu": (0x0A80, 0x0AFF),  # Gujarati
        "pa": (0x0A00, 0x0A7F),  # Punjabi (Gurmukhi)
        "ur": (0x0600, 0x06FF),  # Urdu (Arabic)
    }

    if language not in indic_ranges:
        return True  # Not an Indic script, skip validation

    start, end = indic_ranges[language]
    indic_char_count = 0
    valid_indic_count = 0
    total_chars = 0
    ascii_only = True

    for char in text:
        code = ord(char)
        total_chars += 1
        
        if code >= 0x0080:  # Non-ASCII
            ascii_only = False
            indic_char_count += 1
            if start <= code <= end:
                valid_indic_count += 1

    # For Indic languages, we expect Indic script characters
    # If it's ASCII-only or mostly ASCII, it's likely English/garbage
    if ascii_only or indic_char_count == 0:
        print(f"Indic text validation failed: no Indic script characters for {language}")
        return False

    # At least 70% of non-ASCII characters should be valid for the target script
    if indic_char_count > 0:
        valid_ratio = valid_indic_count / indic_char_count
        if valid_ratio < 0.7:
            print(
                f"Indic text validation failed: only {valid_ratio:.1%} valid {language} characters"
            )
            return False

    return True


def _get_decode_options(language: str) -> dict:
    is_english = language == "en"
    is_indic = language in _NON_ENGLISH_PROMPTS

    # Non-English speech benefits from slightly stronger decoding and softer filters.
    # Indic languages need even more aggressive decoding due to script complexity.
    options = {
        "language": language,
        "task": "transcribe",
        "fp16": False,
        "verbose": False,
        "temperature": 0.0 if is_english else (0.0, 0.1),
        "condition_on_previous_text": False,
        "no_speech_threshold": 0.5 if is_english else (0.7 if is_indic else 0.6),
        "logprob_threshold": -0.8 if is_english else (-2.0 if is_indic else -1.2),
        "compression_ratio_threshold": 2.0,
    }

    if not is_english:
        # Indic languages benefit from deeper beam search
        options["beam_size"] = 10 if is_indic else 5
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

            # Use decode options to determine thresholds (already language-aware)
            is_indic = language in _NON_ENGLISH_PROMPTS
            no_speech_cutoff = decode_options.get("no_speech_threshold", 0.6)
            logprob_cutoff = decode_options.get("logprob_threshold", -1.0)

            if avg_no_speech_prob > no_speech_cutoff:
                print(
                    "Whisper STT dropped transcript due to high no_speech_prob: "
                    f"{avg_no_speech_prob:.3f} (cutoff: {no_speech_cutoff})"
                )
                return None

            if avg_logprob < logprob_cutoff:
                print(
                    "Whisper STT dropped transcript due to low confidence avg_logprob: "
                    f"{avg_logprob:.3f} (cutoff: {logprob_cutoff})"
                )
                return None

            # Log confidence metrics for Indic languages
            if is_indic:
                print(
                    f"Indic transcription confidence - no_speech_prob: {avg_no_speech_prob:.3f}, "
                    f"avg_logprob: {avg_logprob:.3f}"
                )

        text = result.get("text", "").strip()
        if not text:
            print("Whisper STT: no text returned")
            return None

        # Validate Indic text to catch garbled output
        if not _validate_indic_text(text, language):
            print(f"Whisper STT: Indic text validation failed for {language}")
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