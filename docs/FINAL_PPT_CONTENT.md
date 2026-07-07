# ConverseNow: Slide-by-Slide Presentation Content Outline
This document contains the exact slide titles, bullet points, speaker notes, and image/diagram placeholders for a **10-slide capstone presentation** to your faculty.

---

### Slide 1: Title Slide (Project Introduction)
* **Title**: **ConverseNow**
* **Subtitle**: Real-Time Assistive Translation and Indian Sign Language (ISL) Avatar Interpretation System
* **Bullet Points**:
  * An event-driven, low-latency client-server assistive tool.
  * Designed to bridge the communication gap for the hearing-impaired.
  * Translates vocal regional Indian speech into 3D sign animations.
* **Image/Visual Placeholder**:
  * *[Center]*: A clean project logo or a high-quality screenshot of the Unity 3D Avatar standing next to the subtitle panel.
* **Presenter Notes**:
  * Welcome the panel. Introduce the team members (Aditya, Moulika, Jaahnavi, Sophie, Shanmukhee). State the core goal: to build a real-time, multilingual translator driving a sign language avatar.

---

### Slide 2: The Accessibility Problem & Motivation
* **Title**: The Accessibility Challenge in India
* **Bullet Points**:
  * **Social Barrier**: The hearing-impaired struggle to communicate with the vocal majority at public kiosks, transit hubs, and hospitals.
  * **Multilingual Gap**: Standard sign-translation platforms are built primarily for English; India requires support for diverse regional scripts.
  * **Conversational Latency**: Existing systems process only pre-recorded full audio files, making conversational flow impossible.
* **Image/Visual Placeholder**:
  * *[Right-half]*: A diagram illustrating the barrier (Vocal Speaker $\leftrightarrow$ Lack of Sign Interpreter $\leftrightarrow$ Hearing-Impaired Individual).
* **Presenter Notes**:
  * Highlight the lack of regional language sign interpretation tools. Emphasize that ConverseNow acts as a real-time digital interpreter on standard hardware.

---

### Slide 3: The Proposed Solution
* **Title**: The ConverseNow Ecosystem
* **Bullet Points**:
  * **Stateless Pipeline**: Server operates completely in-memory for speed and security; no user databasing required.
  * **Low-Latency Streaming**: Ingests microphone audio continuously in 200ms increments.
  * **Local AI Execution**: Local STT and cascading gloss generation ensure high privacy and reduced cost.
  * **Humanoid Visual Output**: Drives a customized, highly visible Unity humanoid avatar playing standard `.anim` sign files.
* **Image/Visual Placeholder**:
  * *[Bottom]*: A horizontal block diagram showing the 3 core phases: Audio Capture $\rightarrow$ AI Translation Server $\rightarrow$ 3D Animation Playback.
* **Presenter Notes**:
  * Outline how the client and server divide the work: Unity handles microphone captures and animator outputs, while FastAPI coordinates the language modeling.

---

### Slide 4: System Architecture & Data Flow
* **Title**: System Architecture
* **Bullet Points**:
  * **Client-Server communication**: Powered by asynchronous C# and Python WebSockets.
  * **Event-Driven Router**: `/ws/audio` routes live audio streams, processes configs, and sends back structured metadata.
  * **Async Offloading (`asyncio.to_thread`)**: Heavy tasks (Whisper, Translation, Gloss Parsing) run on worker threads to keep the WebSocket connection responsive.
* **Image/Visual Placeholder**:
  * *[Center]*: The Mermaid sequence diagram or block architecture diagram from `SYSTEM_ARCHITECTURE.md`.
* **Presenter Notes**:
  * Explain the thread-pool configuration. Point out that running Whisper in the main thread blocks WebSocket heartbeats, which is why `to_thread()` was implemented.

---

### Slide 5: Voice Activity Detection (VAD) & Audio Streaming
* **Title**: Speech Activity Detection (SAD)
* **Bullet Points**:
  * **PCM16 Encoding**: Unity captures floats and scales them to 16-bit signed shorts (PCM16, 16kHz, Mono).
  * **RMS Energy Formula**: Backend calculates audio amplitude on incoming chunks:
    $$\text{RMS} = \sqrt{\frac{1}{N} \sum x_i^2}$$
  * **Segmentation Heuristics**:
    * Energy threshold: `400` (delineates speech from silence).
    * Silence timer: `800ms` (triggers transcription).
    * Max limit: `6000ms` (forces buffer write to avoid memory leak).
* **Image/Visual Placeholder**:
  * *[Right-half]*: A state machine diagram (the state diagram from `SYSTEM_ARCHITECTURE.md`) showing transitions between listening, speech started, and finalization.
* **Presenter Notes**:
  * Explain that VAD happens on-the-fly without heavy models. The `rms_pcm16` calculation is extremely lightweight, ensuring minimal CPU overhead.

---

### Slide 6: Local Speech-to-Text via Whisper
* **Title**: Local STT & Indic Steering
* **Bullet Points**:
  * **Whisper Model**: Locally hosted Whisper (`small` model) runs on PyTorch.
  * **Prompt Steering**: Native script prompts (e.g. Devanagari templates) steer the model to output regional characters.
  * **Unicode Validation**: Validates script blocks (e.g. Devanagari `0x0900-0x097F`). Rejects ASCII translations/noise.
* **Image/Visual Placeholder**:
  * *[Right-half]*: Table showing language locale codes, native Unicode scripts, and sample prompt strings.
* **Presenter Notes**:
  * Highlight the script validation. Explain how we prevent Whisper from outputting English translations or repeating gibberish when the user breathes into the mic.

---

### Slide 7: Machine Translation (SarvamAI)
* **Title**: Multilingual Translation Engine
* **Bullet Points**:
  * **Regional API**: Integrates **SarvamAI's** `sarvam-translate:v1` model.
  * **Dual Translation Pipeline**:
    * Translates regional transcript (e.g., Hindi) to target language for subtitle display.
    * Translates regional transcript to English to serve as the base for sign matching.
  * **Graceful Degradation**: Catches API key/connection errors and passes source text forward to prevent application crashes.
* **Image/Visual Placeholder**:
  * *[Center]*: Code snippet showing translation try-except block handling `ForbiddenError` and caching API states.
* **Presenter Notes**:
  * Emphasize the API key fallback design. Even if the network drops or API limits are hit, the application degrades gracefully instead of throwing exceptions.

---

### Slide 8: Cascade Gloss Translation Engine
* **Title**: Cascade Gloss Translation
* **Bullet Points**:
  * **Stop Word Filter**: Removes auxiliary grammar (`is`, `the`, `to`) carrying no semantic meaning in sign language.
  * **Heuristic Matching Steps**:
    1. *Exact match* in local dictionary.
    2. *Substring match* (length $\ge$ 3) for compound words.
    3. *Similarity mapping* (difflib SequenceMatcher $\ge$ 0.75).
    4. *Fingerspelling fallback* (letter-by-letter spelling).
* **Image/Visual Placeholder**:
  * *[Right-half]*: Flowchart showing the cascade steps from token input to animation output.
* **Presenter Notes**:
  * Explain that fingerspelling is a crucial fallback. If the user mentions a name like "Aditya", the system spells it out using characters A-D-I-T-Y-A.

---

### Slide 9: Unity Playback & UI Synchronization
* **Title**: Avatar Playback & Subtitle Manager
* **Bullet Points**:
  * **Length Cache**: Unity builds a runtime dictionary of animation clip lengths from the Animator Controller to handle timing dynamically.
  * **Animator Cross-Fades**: Transitions between sign animations smoothly using `CrossFade(gloss, 0.1f)`.
  * **Fingerspelling Flicker Sync**: Displays a static `"Fingerspelled-<WORD>"` subtitle while the avatar animates individual letters.
* **Image/Visual Placeholder**:
  * *[Right-half]*: Code snippet showing `PlaySequenceRoutine` and the call to `UpdateActiveGloss()`.
* **Presenter Notes**:
  * Explain how the fingerspelling display works. If the avatar signs "M-Y", the UI displays "Fingerspelled-MY" statically, preventing the text label from flickering rapidly.

---

### Slide 10: Testing, Validation & Contributions
* **Title**: Testing and Team Contributions
* **Bullet Points**:
  * **Offline Test Suites**: `test_gloss_generation.py` (mapping and tokenization) and `test_whisper_indic.py` (STT prompts) passed (100% success).
  * **Development Contributions**:
    * *Aditya*: Backend Websockets, VAD, Whisper STT prompts, Gloss parser, async threading.
    * *Moulika*: Unity workspace setup, UI layouts, `AudioStreamer.cs` microphone streams.
    * *Jaahnavi*: Humanoid rigging, Playback Manager, animation debugging.
    * *Sophie*: MediaPipe tracking pipelines, Blender joint edits, retargeting.
    * *Shanmukhee*: Dataset curation, rig customization, clip validations.
* **Image/Visual Placeholder**:
  * *[Right-half]*: Screengrab of the test execution results in the terminal.
* **Presenter Notes**:
  * Summarize the validation work. Conclude by highlighting that the collaborative workflow successfully integrates AI model layers with real-time Unity visuals.
