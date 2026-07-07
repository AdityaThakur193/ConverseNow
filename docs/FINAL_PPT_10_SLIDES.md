# ConverseNow: 10-Slide Technical Codebase Presentation Outline

This outline presents the project from a purely technical, code-centric perspective, focusing entirely on the **FastAPI Backend (Python)** and the **Unity Client (C#)** files, architectures, and data structures.

---

### Slide 1: Title Slide (System Overview)
* **Title**: **ConverseNow: Technical Deep Dive**
* **Subtitle**: Architectural Design & Source Code Analysis of the Real-Time Translation Pipeline
* **Content**:
  * **System Layout**: Client-Server via ASGI WebSockets.
  * **Backend**: FastAPI (Python), PyTorch (Whisper), SarvamAI API.
  * **Frontend**: Unity 6, Humanoid 3D Animator, C# WebSockets.
* **Visual Element**: Widescreen layout with the System Pipeline block diagram on the right.
* **Presenter Script**:
  * "Hello team. Today we are conducting a technical walk-through of the ConverseNow codebase, diving into the asynchronous WebSocket pipeline that connects our Python backend services with the Unity avatar client."

---

### Slide 2: High-Level Architecture & WebSockets Protocol
* **Title**: System Architecture & WebSocket Protocol
* **Content**:
  * **Bilateral Connection**: Established at `/ws/audio` (FastAPI) and initialized by `AudioStreamer.cs` (Unity).
  * **Stateless Pipeline**: In-memory event loop processing; no database writes to minimize latency.
  * **Configuration Payload**: Client sends target configuration message:
    `{"type": "config", "src_lang": "hi-IN", "tgt_lang": "en-IN"}`
  * **Response Payload**: Backend returns transcription, translation, and animation gloss metadata.
* **Visual Element**: Mermaid sequence diagram mapping messages from client to server (from `SYSTEM_ARCHITECTURE.md`).
* **Presenter Script**:
  * "Our architecture is built on a real-time event loop. Upon connection, the Unity client sends a JSON configuration packet defining the source and target languages. The backend then processes binary audio packages and responds with a unified JSON payload."

---

### Slide 3: Frontend: Audio Capture & Ingestion (`AudioStreamer.cs`)
* **Title**: Frontend: Audio Capture & PCM16 Streaming
* **Content**:
  * **Mic Sampling**: Captures microphone input in a circular buffer at **16kHz, Mono, 16-bit Depth**.
  * **PCM16 Encoding**: Converts raw float audio frames to signed 16-bit shorts, serializes them into bytes, and streams them in 200ms chunks.
  * **Connection Lifecycle**: Normalizes server endpoints, handles connection drops, and toggles status indicators.
* **Visual Element**: Code snippet of the float-to-short conversion loop inside `AudioStreamer.Update()`.
* **Presenter Script**:
  * "The entry point of our frontend is `AudioStreamer.cs`. It handles microphone interface capture. It converts Unity's default float arrays into signed 16-bit PCM bytes and streams them over the socket in 200ms increments."

---

### Slide 4: Backend: WebSocket Router & Thread Offloading (`main.py`)
* **Title**: Backend: WebSocket Router & Async Offloading
* **Content**:
  * **FastAPI WebSocket Consumer**: Handles persistent loop connections and manages client disconnect exceptions.
  * **Event Loop Blocking Fix**: Offloads heavy synchronous execution tasks (`transcribe_wav`, `translate_text`, `generate_gloss_sequences`) to separate threads.
  * **Implementation**: Uses Python's **`asyncio.to_thread()`** to prevent CPU-bound model tasks from locking up the main async event loop.
* **Visual Element**: Code block showing `await asyncio.to_thread(transcribe_wav, ...)` usage inside `main.py`.
* **Presenter Script**:
  * "Because FastAPI runs on an asynchronous event loop, running heavy ML model tasks synchronously would block all websocket traffic. We solve this by offloading transcription, translation, and gloss parsing to a worker pool using `asyncio.to_thread`."

---

### Slide 5: Backend: Speech Activity Detection (SAD) Heuristics
* **Title**: Backend: Speech Activity Detection (SAD)
* **Content**:
  * **RMS Calculation**: Computes voice signal amplitude on incoming chunks:
    $$\text{RMS} = \sqrt{\frac{1}{N} \sum x_i^2}$$
  * **Speech Segmentation**:
    * Energy threshold: `400` (delineates speech from silence).
    * Silence timer: `800ms` (triggers transcription).
    * Max safety threshold: `6000ms` (forces processing to prevent buffers from growing too large).
  * **CLI Diagnostics**: Prints real-time voice volume updates to verify mic streaming during runtime.
* **Visual Element**: State machine transition diagram for SAD states (Idle, Speech Started, Counting Silence, Finalize).
* **Presenter Script**:
  * "Instead of resource-heavy VAD models, the server calculates Root Mean Square on the raw bytes. If volume exceeds 400, speech begins. After 800ms of silence, the audio buffer is packed into WAV format for transcription."

---

### Slide 6: Backend: Speech-to-Text (STT) Service (`stt_service.py`)
* **Title**: Backend: Whisper STT & Indic Steering
* **Content**:
  * **Inference Engine**: Wraps local OpenAI Whisper (`small` model) on PyTorch.
  * **Prompt Steering**: Steers Whisper using native initial prompts (e.g. Devanagari script for Hindi) to force native script output.
  * **Unicode Script Verification**: Validates block ranges (e.g. `0x0900-0x097F`). Rejects ASCII translations or hallucinations when Indic modes are active.
* **Visual Element**: List of regional Indic prompts and their Unicode blocks mapped in `stt_service.py`.
* **Presenter Script**:
  * "Our speech-to-text service in `stt_service.py` loads Whisper locally. To ensure regional scripts are output accurately without english hallucinations, we inject script-native initial prompts and validate the output against native Unicode ranges."

---

### Slide 7: Backend: Translation Service (`translation_service.py`)
* **Title**: Backend: Translation & Graceful API Fallbacks
* **Content**:
  * **Sarvam Translation API**: Integrates `sarvam-translate:v1` model to translate regional scripts.
  * **Dual Translation Pipeline**:
    * Translates text to target regional language (subtitles).
    * Translates text to English (base language for sign gloss translation).
  * **Failsafe Cache**: Checks keys and handles `ForbiddenError` failures gracefully by returning source text.
* **Visual Element**: Code snippet showing translation try-except wrapper handling connection and credential exceptions.
* **Presenter Script**:
  * "Translation is handled by `translation_service.py` via the SarvamAI API. The transcript is translated twice: once to the target language and once to English. If the API experiences key exhaustion, the pipeline gracefully falls back to the original text."

---

### Slide 8: Backend: Cascade Gloss Generator (`gloss_generation_service.py`)
* **Title**: Backend: Cascade Gloss Translation Engine
* **Content**:
  * **Stop Word Removal**: Eliminates auxiliary grammar (`is`, `the`, `to`) mapped to `None` in `GLOSS_DICTIONARY`.
  * **Heuristic Resolver**:
    1. *Exact match* in local vocabulary.
    2. *Substring match* (restricted to keys $\ge$ 3 characters to avoid short letter collisions).
    3. *Similarity mapping* (difflib SequenceMatcher ratio $\ge$ 0.75).
    4. *Fingerspelling fallback* (A-Z character spelling).
* **Visual Element**: Flowchart showing the cascade steps from token input to animation output.
* **Presenter Script**:
  * "`gloss_generation_service.py` maps English text to available sign clips. It filters out grammatical stop words and runs a cascading match. If no match is found, it falls back to fingerspelling, splitting the word into letter-by-letter animations."

---

### Slide 9: Frontend: Sign Playback Manager (`ISLPlaybackManager.cs`)
* **Title**: Frontend: Avatar Rig & Playback Controller
* **Content**:
  * **Clip Length Cache**: Scans loaded humanoid animations inside the Animator Controller at launch to cache timing.
  * **Smooth Transitions**: Humanoid joints cross-fade smoothly between clips using `animator.CrossFade(gloss, 0.1f)`.
  * **Fingerspelling UI Sync**: Displays a static `"Fingerspelled-<WORD>"` subtitle while spelling animations run, preventing rapid text flicker.
* **Visual Element**: Diagram showing the animation queue execution loop.
* **Presenter Script**:
  * "When the Unity client receives the gloss list, `ISLPlaybackManager.cs` cross-fades between the animation clips. During fingerspelling, the subtitle manager displays a static 'Fingerspelled-WORD' label so that text doesn't flicker rapidly on screen."

---

### Slide 10: Frontend: UI bindings & Subtitle Sync (`SubtitleManager.cs`)
* **Title**: Frontend: Subtitle UI & Scene Bindings
* **Content**:
  * **Scene-Wide Binding**: Automatically queries TextMeshPro text fields in children (or the entire scene if needed) during validation to bind references.
  * **JSON Parser**: Parses backend payload into `BackendMessage` class.
  * **Text Synchronization**: Updates subtitle texts and status labels, and clears gloss text fields.
* **Visual Element**: Code snippet of the `AutoBindTextFields()` method and the `BackendMessage` struct definition.
* **Presenter Script**:
  * "To ensure the UI links seamlessly, `SubtitleManager.cs` scans the scene for TMPro fields. It parses the WebSocket JSON responses and updates subtitle labels, status fields, and animates active gloss labels in sync with the avatar."
