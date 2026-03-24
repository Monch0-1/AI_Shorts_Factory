# GEMINI.md - Project Mandates & Instructions

This file contains foundational mandates for Gemini CLI when working on the **AI Short-Video Generator** project. These instructions take absolute precedence over general workflows.

## 🎯 Project Overview
An automated pipeline transforming topics into short-form videos using **Google Gemini** for scripts, **ElevenLabs** for narration, and **MoviePy** for assembly.

## 🛠️ Core Mandates (High Priority)
1.  **Session Start Protocol:**
    *   **MUST** read `project_instructions.md` and `general_instructions.md` at the beginning of every session.
    *   **MUST** provide a brief acknowledgment in the console confirming understanding of project-specific and general instructions.
2.  **Design-First Approval:**
    *   For any non-trivial code modification, you **MUST** present a design plan, technical rationale, and a summary of suggested changes.
    *   Implementation **ONLY** proceeds after explicit user approval.
3.  **Environment Constraints:**
    *   **Directory Lock:** Stay within `C:\Users\Monch\PycharmProjects\PythonProject`. Do not work in other directories.
    *   **Branch Tracking:** The current active branch is `Super_Edits_SFX`. If the branch changes via `git checkout`, update `general_instructions.md` immediately.
4.  **Session End Protocol:**
    *   **MUST** update the "Session Summary" section in `project_instructions.md` when the session ends or upon request.

## 🏗️ Engineering Standards
1.  **Library Management (SFX):**
    *   Follow the **convention-based folder hierarchy** (`category/intent_tag/filename.mp3`).
    *   Use `manage_sfx.py` for all SFX operations (Ingest, Sync, List, Reset).
    *   The folder structure is the source of truth; sync to DB and YAML accordingly.
2.  **Data Modeling:**
    *   Transition towards consistent use of `Pydantic` (currently mixed with `dataclasses`).
    *   `script_models.py` uses Pydantic; `video_models.py` uses dataclasses (Technical Debt to be addressed).
3.  **Code Hygiene:**
    *   Use top-level imports (avoid inline imports like `import math` inside functions).
    *   Standardize FFmpeg configurations.
    *   Replace `print` statements with a standard `logging` framework.
4.  **Testing & Validation:**
    *   **Mandatory:** Every change must be accompanied by updated or new tests in `CreateShorts_Test/`.
    *   Verify behavioral correctness before concluding a task.

## 🔄 Active Workflow: Professional SFX Editor
*   **Precision Control:** `HighlightDTO` includes `placement` (start/end), `offset_seconds`, and `volume_modifier`.
*   **Audio Assembly:** Logic in `create_audio.py` must interpret these fields for J-cuts, reaction beats, and volume ducking.
*   **Toggle logic:** Respect the `include_sfx` flag in `VideoRequest` and `VideoOptions`.

## 📌 Project Structure
*   `Create_New_Short.py`: Main entry point for video generation.
*   `manage_sfx.py`: CLI tool for SFX management.
*   `CreateShorts/`: Core logic (Models, Services, Data_Gen).
*   `CreateShorts_Test/`: All project tests.
*   `resources/sfx/`: Organized SFX library.
