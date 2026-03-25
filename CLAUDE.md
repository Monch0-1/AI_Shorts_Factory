# CLAUDE.md - Project Directives for Claude Code

## Session Start Protocol
At the start of every session, Claude MUST:
1. Read `C:\Users\Monch\PycharmProjects\general_instructions.md` for environment constraints.
2. Read `project_instructions.md` for current project state, pending tasks, and session history.
3. Acknowledge understanding of both files before proceeding.

## Session End Protocol
When the user signals session end or requests a summary update, Claude MUST update the "Session Summary" section in `project_instructions.md`.

---

## Project Overview
An automated pipeline that transforms topics into short-form videos:
- **Script Generation:** Google Gemini
- **Narration & SFX:** ElevenLabs
- **Video Assembly:** MoviePy

---

## Environment Constraints
- **Directory Lock:** Stay within `C:\Users\Monch\PycharmProjects\PythonProject`. Never work in other directories.
- **Branch Tracking:** Active branch is `Super_Edits_SFX`. If changed via `git checkout`, update `general_instructions.md` immediately.
- **Test Runner:** Use `.\.venv\Scripts\pytest.exe` — do NOT rely on system PATH.

---

## Core Mandates

### Design-First Approval
For any non-trivial code change, Claude MUST:
1. Present a design plan, technical rationale, and summary of changes.
2. Wait for explicit user approval before implementing.

### Testing
- Every code change requires updated or new tests in `CreateShorts_Test/`.
- Verify behavioral correctness before concluding any task.

### Code Hygiene
- Use top-level imports (no inline imports inside functions).
- Replace `print` statements with Python `logging` framework.
- Standardize FFmpeg configuration — no redundant configs.
- Prefer Pydantic models over dataclasses (ongoing migration).

---

## Project Structure
```
PythonProject/
├── Create_New_Short.py         # Main entry point
├── manage_sfx.py               # CLI tool for SFX library management
├── CreateShorts/
│   ├── Models/                 # Pydantic & data models
│   ├── Services/               # Business logic (SFXService, providers, etc.)
│   ├── Data_Gen/               # Script & audio generation
│   ├── Interfaces/             # Abstract interfaces (ISFXProvider, etc.)
│   └── ContextualDataService/  # Contextual data utilities
├── CreateShorts_Test/          # All project tests
├── resources/sfx/              # SFX library (category/intent_tag/filename.mp3)
├── project_instructions.md     # Session log & task tracking
├── general_instructions.md     # (parent dir) Environment constraints
└── CLAUDE.md                   # This file
```

---

## SFX Engineering Standards
- Follow convention-based folder hierarchy: `category/intent_tag/filename.mp3`
- Use `manage_sfx.py` for all SFX operations (Ingest, Sync, List, Reset)
- Folder structure is the source of truth — sync to DB and YAML accordingly

### SFX Provider Architecture
- `ISFXProvider`: Abstract interface decoupling selection sources
- `LocalSFXProvider`: Semantic scoring — Category Match 50%, Trait Intersection 40%, Variety 10%; Quality Gate: 60/100
- `ElevenLabsSFXProvider`: AI fallback for high-fidelity generation via API
- `SFXService`: Coordinator orchestrating Local → AI fallback flow

### SFX Fields in HighlightDTO
- `category`, `desired_traits`, `beat_delay`, `placement` (start/end), `offset_seconds`, `volume_modifier`

---

## Active Pending Work
1. **AssetProcessor:** Audio normalization (-6dB) and duration capping (3s) via `pydub`
2. **ElevenLabs SFX Validation:** Live API testing pending env var verification
3. **Gemini Prompt Updates:** Include `desired_traits`, `category`, `beat_delay` in JSON script output
4. **Comfort Gap Logic:** Implement `beat_delay` handling in `create_audio.py`
5. **FastAPI Migration:** Planning phase — transition core pipeline to FastAPI

---

## Technical Debt (Lower Priority)
- Unify all DTOs to Pydantic (`video_models.py` still uses dataclasses)
- Rename `text_to_speach.py` → `text_to_speech.py`
- Decompose `create_final_video` in `mix_assets.py` into testable units
- Replace `Image.ANTIALIAS` with `Image.Resampling.LANCZOS` in `mix_assets.py`
- Centralize constants into a `ConfigService`
