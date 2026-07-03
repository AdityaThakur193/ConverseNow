# ConverseNow: Software Requirements Specification (SRS)

This document outlines the functional, non-functional, and system requirements for the ConverseNow real-time translation system.

---

## 1. System Requirements & Environment Constraints
* **Operating System**: Windows 10/11 or Ubuntu Linux.
* **Python Runtime**: Python 3.8+ (tested on Python 3.13).
* **System Utilities**: **FFmpeg** installed and added to the System PATH (required for Whisper audio decoding).
* **Machine Learning Runtime**: PyTorch (with CUDA enabled for GPU-based fast Whisper inference).
* **Client Runtime**: Unity 6 Editor (or stand-alone builds).

---

## 2. Functional Requirements

### FR-1: Real-Time Audio Streaming
* The client must capture microphone input at **16kHz, Mono, 16-bit PCM** format.
* The client must stream audio in small buffers (200ms) to the server via WebSockets to minimize latency.

### FR-2: Intelligent Utterance Segmentation
* The server must analyze incoming frames on-the-fly and calculate the signal energy (RMS).
* The server must segment and finalize an utterance when:
  * Silence (energy $< 400$) is detected for more than `800ms` following active speech.
  * The total duration of active speech reaches `6000ms` (safety limit).

### FR-3: Multilingual Transcription & Validation
* The server must transcribe speech in English and 10 regional Indian scripts (Devanagari, Telugu, Tamil, Malayalam, Kannada, Gurmukhi, Arabic/Urdu, etc.) using local Whisper inference.
* The system must reject noise/ASCII transcripts when an Indic regional script was expected.

### FR-4: API-Based Text Translation
* The server must translate the finalized transcription into:
  * The target language requested by the client (for UI subtitles).
  * English (for sign language gloss translation).

### FR-5: Cascade Gloss Translation
* The system must map English text into a sequence of ISL glosses using a cascading match checklist:
  * Omit grammatical stop words (e.g., `"is"`, `"to"`, `"the"`).
  * Match exact dictionary terms.
  * Match sub-words/substrings (length $\ge$ 3).
  * Match similar terms (similarity score $\ge$ 0.75).
  * Spell out remaining proper nouns/unrecognized words letter-by-letter.

### FR-6: Synchronized Animation Playback
* The Unity client must parse the backend JSON payload.
* The client must play back corresponding animation clips in sequence, adjusting wait timers to match the length of each clip.
* The client must display the corresponding gloss display label (e.g., `"HELLO"` or `"Fingerspelled-WORLD"`) in real time as the animation plays.

---

## 3. Non-Functional Requirements

### NFR-1: Performance & Latency
* The system must finalize translation and return the JSON response in less than **1.5 seconds** from the time the user stops speaking.

### NFR-2: Thread Safety & Concurrency
* The backend must use thread-pool execution (`asyncio.to_thread`) for blocking operations (transcription, translation) so that the event loop can handle heartbeats and concurrent socket events.

### NFR-3: Fault Tolerance & Graceful Degradation
* If the SarvamAI API translation key is missing or invalid, the backend must catch the failure, log it, and return the original transcript to keep the WebSocket stream running.
* If a specific animation clip length cannot be cached in Unity, the playback manager must fall back to a `defaultGlossDuration` (1.0 second) to prevent sequence crashes.
