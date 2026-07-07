# ConverseNow: Project Synopsis

## 1. Project Title
**ConverseNow**: Real-Time Assistive Translation and Indian Sign Language (ISL) Interpretation System

---

## 2. Abstract
Communication between hearing-impaired individuals who use sign language and the vocal majority remains a significant accessibility barrier. This gap is especially pronounced in multilingual societies like India, where regional dialects add complexity. 

**ConverseNow** is an end-to-end, low-latency assistive system that bridges this gap. It captures vocal speech in English or one of 10 regional Indian languages, transcribes and translates it, generates corresponding Indian Sign Language (ISL) glosses, and plays the matching animations on a 3D avatar client in real time. 

By employing local Speech-to-Text inference and a robust cascade mapping dictionary with automatic fingerspelling fallbacks, the system provides a responsive, offline-capable tool for assistive communication.

---

## 3. Problem Statement & Motivation
* **Communication Gap**: Signing individuals cannot easily communicate with non-signing individuals in daily public spaces (hospitals, banks, transit stations).
* **Multilingual Complexity**: Standard sign translation systems are built primarily for English. An assistive tool in India must support regional scripts (Hindi, Tamil, Telugu, etc.).
* **Technical Latency**: Existing translation pipelines require waiting for an entire audio recording to finish before starting processing, making conversation feel unnatural.

---

## 4. Proposed Solution & Objectives
ConverseNow solves these issues by establishing a real-time event-driven translation pipeline:
1. **Real-time Streaming**: Ingests continuous microphone streams in 200ms increments.
2. **Speech Activity Detection (SAD)**: Uses energy-based segmenting locally to finalize utterances automatically.
3. **Local High-Fidelity STT**: Uses a locally run OpenAI Whisper model tuned with language-specific script-native prompts to produce accurate regional translations.
4. **Cascade Gloss Translation**: Converts English translations to sign glosses using exact, substring, similarity, or fingerspelling heuristics.
5. **Interactive Avatar Engine**: Drives a 3D Unity Avatar that executes animations smoothly and displays subtitles in sync.

---

## 5. Scope & Technology Stack
* **Client App**: Unity 6, TextMeshPro, C# WebSockets.
* **Server Backend**: Python 3.8+, FastAPI, Uvicorn (ASGI).
* **Inference Models**: Local OpenAI Whisper (`small` model), PyTorch.
* **Translation APIs**: SarvamAI REST Client API (`sarvam-translate:v1`).
* **Supported Languages**: English (`en-IN`), Hindi (`hi-IN`), Marathi (`mr-IN`), Telugu (`te-IN`), Tamil (`ta-IN`), Kannada (`kn-IN`), Malayalam (`ml-IN`), Bengali (`bn-IN`), Gujarati (`gu-IN`), Punjabi (`pa-IN`), Urdu (`ur-IN`).
