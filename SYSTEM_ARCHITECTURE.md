# ConverseNow: System Architecture & Design Document (SADD)

This document provides a detailed breakdown of the ConverseNow architecture, describing components, data flows, state machines, and schemas.

---

## 1. High-Level Data Flow & Pipeline Architecture
The diagram below maps out how raw vocal input from the Unity client is transformed, analyzed, and processed into sign animations.

```mermaid
flowchart TD
    subgraph Client [Unity Client]
        Mic[Microphone Input] -->|Float Array| Scale[PCM16 Encoder]
        Scale -->|Binary Packets 200ms| WS_Send[WebSocket Client]
        WS_Recv[WebSocket Client] -->|Parse JSON| SubUI[Subtitle UI]
        WS_Recv -->|Glosses & Display| Playback[ISL Playback Manager]
        Playback -->|Cross-Fade Clips| Anim[3D Avatar Animator]
    end

    subgraph Server [FastAPI Backend]
        WS_Send -.->|Network Stream| WS_Router[WS /ws/audio Route]
        WS_Router -->|200ms chunks| VAD[RMS Energy Calculator]
        VAD -->|Accumulate bytes| Buf[Audio Buffer]
        VAD -->|Silence > 800ms| Finalize[PCM-to-WAV converter]
        Buf --> Finalize
        Finalize -->|WAV Bytes| STT[Whisper STT Service]
        STT -->|Transcript| Trans[Sarvam Translation Service]
        Trans -->|Target Text| WS_Out[Response Builder]
        Trans -->|English Text| Gloss[Gloss Generation Service]
        Gloss -->|Glosses & Display Labels| WS_Out
        WS_Out -->|JSON Response| WS_Router
        WS_Router -.->|Network Send| WS_Recv
    end
```

---

## 2. Speech Activity & Connection State Machine
The backend operates a state-driven WebSocket consumer. The diagram below illustrates how audio segments are identified and sent for translation.

```mermaid
stateDiagram-v2
    [*] --> Idle: WebSocket Connected
    Idle --> Listening: Stream Started
    Listening --> Speech_Started: RMS Energy > 400
    Speech_Started --> Speech_Started: RMS Energy > 400 (speech_ms += 200ms)
    Speech_Started --> Silence_Detected: RMS Energy <= 400
    Silence_Detected --> Speech_Started: RMS Energy > 400 (silence_ms = 0)
    Silence_Detected --> Finalize_Utterance: silence_ms >= 800ms OR speech_ms >= 6000ms
    Finalize_Utterance --> In_Progress: Run STT, Translation, Gloss Mapping
    In_Progress --> Idle: send_json() Success
    In_Progress --> [*]: Connection Closed/Disconnection
```

---

## 3. Data Models & JSON Payload Schemas (ER-Equivalent)
Since ConverseNow is a **stateless** translation pipeline, there is no physical SQL/NoSQL database storage. The diagram below represents the logical schema and relationship of the in-memory variables and WebSocket serialization classes.

```mermaid
classDiagram
    class ConfigMessage {
        +string type = "config"
        +string src_lang
        +string tgt_lang
    }
    class BackendMessage {
        +string original
        +string translated
        +string english
        +string[] glosses
        +string[] glosses_display
        +string src_lang
        +string tgt_lang
        +double timestamp
        +bool final
    }
    class GlossDictionary {
        +dict GLOSS_DICTIONARY
        +set AVAILABLE_GLOSSES
        +dict ALPHABET_GLOSS
    }
    class AudioState {
        +bytearray audio_buffer
        +bool speech_started
        +int speech_ms
        +int silence_ms
        +string last_final_transcript
    }

    ConfigMessage ..> AudioState : Updates src/tgt language config
    AudioState ..> BackendMessage : Processed into output
    GlossDictionary ..> BackendMessage : Populates glosses & display
```

---

## 4. Component Details (Python Backend)

### A. Entry Router & WebSocket Handler (`main.py`)
* Manages Client WebSocket connections at `/ws/audio`.
* **Speech Activity Detection (SAD)**: Calculates Root Mean Square (RMS) energy on incoming 200ms chunks using `rms_pcm16`.
* **Utterance Segmentation**: Finalizes the buffer when silence is detected for more than `800ms` (following at least `800ms` of active speech) or when the utterance hits a maximum duration of `6000ms`.
* **Async Thread Offloading**: Runs heavy operations (STT, translation, gloss generation) via `asyncio.to_thread` to ensure the main ASGI event loop is never blocked.

### B. Speech-to-Text (`stt_service.py`)
* Wraps the local **OpenAI Whisper** model.
* **Decoding Optimization**: Utilizes language-specific prompt steering (e.g., feeding native script templates as initial prompts) and parameter overrides (beam size, logprob, and no-speech cutoffs) to improve transcription accuracy.
* **Script Verification**: Validates the Unicode block ranges of the output text against the target language to prevent Whisper from outputting ASCII characters/noise in place of native regional scripts.

### C. Translation Service (`translation_service.py`)
* Integrates with the **SarvamAI Translation API** (`sarvam-translate:v1`).
* Translates the transcription to the target language and also to English (used as the base language for sign mapping).
* Implements dynamic API fail-safe caching to gracefully bypass the translation step if the API key is invalid or expires.

### D. Gloss Translation Service (`gloss_generation_service.py`)
* Resolves the English translation into a list of animation names.
* **Stop Word Omission**: Removes words like `"is"`, `"the"`, `"to"` which carry no semantic weight in sign language.
* **Cascading Logic**:
  1. *Exact match* in local dictionary.
  2. *Substring match* (restricted to keys $\ge$ 3 characters).
  3. *Similarity mapping* (using `difflib.SequenceMatcher` with a strict threshold $\ge$ 0.75).
  4. *Fingerspelling fallback*: Spells out unrecognized words character-by-character.
