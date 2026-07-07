# ConverseNow: Project Contributions & Roles

This document outlines the division of work and specific contributions of each team member to the ConverseNow real-time translation and interpretation system.

---

## 1. Aditya (Backend & Machine Learning Services)
* **Real-Time WebSocket Server**: Developed the FastAPI event-driven WebSocket backend at `/ws/audio` to ingest binary PCM16 audio chunks in 200ms streams.
* **Speech Activity Detection (SAD)**: Designed and implemented the RMS-based energy threshold segmenter to identify active speech and automatically finalize utterances after 800ms of silence.
* **Local Speech-to-Text (STT)**: Integrated the local OpenAI Whisper (`small` model) pipeline, overriding temperature, beam-size, and logprob parameters. Configured script-native prompts to steer Indic orthography.
* **Indic Text Validator**: Programmed Unicode block verification rules to validate script outputs for 10 regional Indian languages and discard garbled/ASCII noise.
* **Sarvam Translation API**: Integrated the SarvamAI REST Client for regional-to-regional text translation, along with key caching mechanisms to handle failures gracefully.
* **Sign Language Gloss Generator**: Built the 4-step cascade translator (Stop Word Filter $\rightarrow$ Exact Match $\rightarrow$ Substring $\rightarrow$ Similarity Fallback $\rightarrow$ Spelling Fallback) mapping English text to animation keys.
* **Async Threading Optimization**: Restructured blocking tasks to run on thread pools using `asyncio.to_thread`, preventing event-loop freezing and allowing graceful disconnect handling.
* **Test Automation Suite**: Created automated tests (`test_gloss_generation.py` and `test_whisper_indic.py`) validating translation logic and Unicode constraints.

---

## 2. Moulika (Unity Setup, UI Controls & User Flow)
* **Unity Client Setup**: Managed the complete configuration of the Unity project, Canvas hierarchies, TextMeshPro assets, and project styling profiles.
* **WebSocket Networking & Audio Capture**: Maintained and integrated `AudioStreamer.cs`, managing raw microphone capture, audio scale filters (scaling floats to signed 16-bit PCM), and direct WebSocket client connections.
* **UI subtitle Integration**: Built and managed `SubtitleManager.cs` to auto-bind text containers, parse WebSocket JSON responses, and display translated subtitles.
* **Speech Control Workflows**: Programmed the start/stop triggers (`StartStopContrller.cs`), control buttons, and particle ripple feedback to toggle audio streaming.
* **Configuration Management**: Designed and structured the translation target language dropdown selectors (`LanguageManager.cs`) and custom font/color controls (`SettingsUI.cs`).

---

## 3. Jaahnavi Neelam (Humanoid Rigging, Playback Systems & Motion Capture)
* **Research & Evaluation**: Conducted a comprehensive study of Indian Sign Language avatar systems, motion capture technologies, and Unity humanoid rigging workflows.
* **MediaPipe Feasibility Analysis**: Extracted body and hand coordinates using MediaPipe and evaluated the feasibility of using landmark coordinates to drive avatar movement in Unity.
* **Motion Capture & FBX Generation**: Converted recorded sign language videos into FBX motion data using DeepMotion and QuickMagic for animation integration.
* **Humanoid Rigging & Animation Playback**: Integrated the humanoid avatar in Unity, configured humanoid rigging and animation controllers, and implemented playback of recorded `.anim` files.
* **Testing & Debugging**: Tested and resolved issues related to avatar movement, bone rotations, hand and finger orientations, and animation synchronization to improve playback accuracy and overall performance.

---

## 4. Sophie (Animation Pipelines & Humanoid Rigging)
* **Research & Selection**: Researched ISL datasets and selected video samples for testing and validation.
* **Animation Pipeline Development**: Developed the `MP4 -> FBX -> .anim -> Unity` pipeline to convert ISL videos into 3D avatar animations.
* **Animation Refinement**: Refined animation files in Blender and XR Animator for smooth, accurate motion.
* **Humanoid Avatar Configuration**: Rigged and configured humanoid avatars in Unity, including manual bone mapping for gesture accuracy.
* **Frame-by-Frame Editing**: Edited hand and finger animations frame-by-frame in Blender to improve natural movement.
* **Motion Retargeting**: Retargeted ISL video movements onto 3D avatars using tracking points.
* **Pose Tracking Tests**: Tested `MediaPipeUnityPlugin` for MP4-based pose tracking and avatar mapping.
* **Import Issue Resolution**: Resolved import issues with `.glb`, `.gltf`, `.fbx`, and `.anim` formats.

---

## 5. Shanmukhee (ISL Animation Dataset, Rig Customization & Playback Validation)
* **ISL Dataset Curation**: Built the project's core Indian Sign Language (ISL) animation dataset by curating and organizing sign animation files.
* **File Extraction & Management**: Extracted `.anim` asset packages from generated animation workflows and configured them as Unity-ready animation clips.
* **Avatar Selection & Customization**: Selected and rigged a customized Unity-compatible humanoid avatar model tailored to sign-language clarity constraints.
* **Animation Tool Benchmarking**: Evaluated various AI-driven animation capture software (DeepMotion, Rokoko, Plask, Move.ai) to optimize sign motion quality.
* **Validation & Testing**: Validated the full set of imported sign clips inside Unity to eliminate clipping errors and ensure high-fidelity animations.
