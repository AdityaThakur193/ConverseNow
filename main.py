import io
import json
import math
import re
import time
from array import array
import sys
import wave
import traceback

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from stt_service import transcribe_wav
from translation_service import translate_text
from gloss_generation_service import generate_glosses, generate_glosses_with_confidence

app = FastAPI()


@app.get("/")
async def root():
    return {"status": "ok", "message": "ConverseNow is live"}


@app.get("/health")
async def health():
    return {"status": "ok", "message": "ConverseNow is live"}


def pcm16_to_wav(
    pcm_bytes: bytes,
    sample_rate: int = 16000,
    num_channels: int = 1,
    sample_width: int = 2,
) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(num_channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buffer.getvalue()


def rms_pcm16(pcm_bytes: bytes) -> int:
    if not pcm_bytes:
        return 0

    usable_length = len(pcm_bytes) - (len(pcm_bytes) % 2)
    if usable_length <= 0:
        return 0

    samples = array("h")
    samples.frombytes(pcm_bytes[:usable_length])

    if sys.byteorder != "little":
        samples.byteswap()

    mean_square = sum(sample * sample for sample in samples) / len(samples)
    return int(math.sqrt(mean_square))


def is_meaningful_text(text: str) -> bool:
    if not text:
        return False

    cleaned = text.strip()
    if not cleaned:
        return False

    fillers = {"uh", "um", "hmm", "mmm", "ah", "oh"}
    if cleaned.lower() in fillers:
        return False

    if len(cleaned) < 3:
        return False

    letters = sum(1 for ch in cleaned if ch.isalpha())
    alnum = sum(1 for ch in cleaned if ch.isalnum())

    if letters == 0:
        return False

    if alnum > 0 and (letters / alnum) < 0.45:
        return False

    if re.fullmatch(r"[\W_]+", cleaned):
        return False

    return True


@app.websocket("/ws/audio")
async def audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Unity connected")

    src_lang = "en-IN"
    tgt_lang = "hi-IN"

    SAMPLE_RATE = 16000
    SAMPLE_WIDTH = 2
    NUM_CHANNELS = 1
    CHUNK_MS = 200
    ENERGY_THRESHOLD = 1100
    SILENCE_MS_TO_END = 800
    MIN_SPEECH_MS = 800
    MAX_UTTERANCE_MS = 6000

    audio_buffer = bytearray()
    speech_started = False
    speech_ms = 0
    silence_ms = 0
    last_final_transcript = ""

    try:
        while True:
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                print("WebSocket disconnect received")
                break

            if "text" in message and message["text"] is not None:
                try:
                    payload = json.loads(message["text"])
                    if payload.get("type") == "config":
                        src_lang = payload.get("src_lang", src_lang)
                        tgt_lang = payload.get("tgt_lang", tgt_lang)
                        print(f"Config updated: src={src_lang}, tgt={tgt_lang}")
                except Exception as e:
                    print(f"Invalid text/config message: {e}")
                continue

            if "bytes" not in message or message["bytes"] is None:
                continue

            data = message["bytes"]
            if not data:
                continue

            audio_buffer.extend(data)

            try:
                rms = rms_pcm16(data)
            except Exception:
                rms = 0

            if rms > ENERGY_THRESHOLD:
                speech_started = True
                speech_ms += CHUNK_MS
                silence_ms = 0
            else:
                if speech_started:
                    silence_ms += CHUNK_MS

            should_finalize = False

            if speech_started and speech_ms >= MIN_SPEECH_MS and silence_ms >= SILENCE_MS_TO_END:
                should_finalize = True

            if speech_started and speech_ms >= MAX_UTTERANCE_MS:
                should_finalize = True

            if should_finalize:
                print(
                    f"Finalizing utterance | speech_ms={speech_ms} silence_ms={silence_ms} bytes={len(audio_buffer)}"
                )

                wav_bytes = pcm16_to_wav(
                    pcm_bytes=bytes(audio_buffer),
                    sample_rate=SAMPLE_RATE,
                    num_channels=NUM_CHANNELS,
                    sample_width=SAMPLE_WIDTH,
                )

                transcript = transcribe_wav(wav_bytes, src_lang=src_lang)

                audio_buffer = bytearray()
                speech_started = False
                speech_ms = 0
                silence_ms = 0

                if not transcript:
                    print("No transcript returned")
                    continue

                transcript = transcript.strip()
                if not is_meaningful_text(transcript):
                    print(f"Ignored weak transcript: {transcript!r}")
                    continue

                if transcript == last_final_transcript:
                    print("Duplicate transcript ignored")
                    continue

                last_final_transcript = transcript

                # Translate to target language
                translated = translate_text(
                    transcript,
                    src_lang=src_lang,
                    tgt_lang=tgt_lang
                ) or transcript

                # Also translate to English for gloss generation
                english_for_glosses = translate_text(
                    transcript,
                    src_lang=src_lang,
                    tgt_lang="en-IN"
                ) or ""

                # Generate ISL glosses from English translation
                glosses = []
                try:
                    if english_for_glosses:
                        glosses = generate_glosses(english_for_glosses)
                        print(f"Generated glosses: {glosses}")
                except Exception as e:
                    print(f"Error generating glosses: {e}")
                    glosses = []

                response = {
                    "original": transcript,
                    "translated": translated,
                    "english": english_for_glosses,  # English version for reference
                    "glosses": glosses,
                    "src_lang": src_lang,
                    "tgt_lang": tgt_lang,
                    "timestamp": time.time(),
                    "final": True,
                }

                await websocket.send_json(response)
                print("Sent final transcript + translation + glosses")

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print("Error in websocket handler:", e)
        traceback.print_exc()
        try:
            await websocket.close()
        except Exception:
            pass


class GlossRequest(BaseModel):
    text: str


@app.post("/api/gloss")
async def get_gloss(payload: GlossRequest):
    text = payload.text
    glosses = generate_glosses(text)
    confidence_data = generate_glosses_with_confidence(text)
    return {
        "glosses": glosses,
        "coverage": confidence_data["coverage"],
        "fallback_words": confidence_data["fallback_words"],
        "unmapped_words": confidence_data["unmapped_words"],
    }