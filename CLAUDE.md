# CLAUDE.md - Project Directives for Claude Code

## Session Start Protocol
At the start of every session, Claude MUST:
1. Read `C:\Users\Monch\PycharmProjects\general_instructions.md` for environment constraints.
2. Read `project_instructions.md` for current project state, pending work, and session history.
3. Acknowledge understanding of both files before proceeding.

## Session End Protocol
When the user signals session end or requests a summary update, Claude MUST update `project_instructions.md` with a session summary entry.

---

## Project Overview
An automated pipeline that transforms topics into short-form videos:
- **Script Generation:** Google Gemini
- **Narration & SFX:** ElevenLabs
- **Video Assembly:** MoviePy

---

## Environment Constraints
- **Directory Lock:** Stay within `C:\Users\Monch\PycharmProjects\PythonProject`. Never work in other directories.
- **Branch Tracking:** Active branch tracked in `general_instructions.md`. If changed via `git checkout`, update `general_instructions.md` immediately.
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
├── Create_New_Short.py              # Main entry point
├── manage_sfx.py                    # CLI tool for SFX library management
├── CreateShorts/
│   ├── Models/                      # Pydantic & data models
│   ├── Services/                    # Business logic (SFXService, providers, etc.)
│   ├── Data_Gen/                    # Script & audio generation
│   ├── Interfaces/                  # Abstract interfaces (ISFXProvider, etc.)
│   ├── Factory/                     # Service factory (real vs mock)
│   └── ContextualDataService/       # Web-search context utilities (under audit)
├── CreateShorts_Test/               # All project tests
├── resources/sfx/                   # SFX library (category/intent_tag/filename.mp3)
├── project_instructions.md          # Live session log, tasks, and tech debt
├── general_instructions.md          # (parent dir) Environment constraints
└── CLAUDE.md                        # This file — immutable directives
```

---

## SFX Engineering Standards
- Follow convention-based folder hierarchy: `category/intent_tag/filename.mp3`
- Use `manage_sfx.py` for all SFX operations (Ingest, Sync, List, Reset, Init)
- Folder structure is the source of truth — sync to DB and YAML accordingly

### SFX Provider Architecture
- `ISFXProvider`: Abstract interface decoupling selection sources
- `LocalSFXProvider`: Semantic scoring — Category Match 50%, Trait Intersection 40%, Variety 10%; Quality Gate: 60/100
- `ElevenLabsSFXProvider`: AI fallback for high-fidelity generation via API
- `SFXService`: Coordinator orchestrating Local → ElevenLabs fallback flow

### SFX Fields in HighlightDTO
- `category`, `desired_traits`, `description`, `beat_delay`, `placement` (start/end), `offset_seconds`, `volume_modifier`

---

## State & Planning
All active work, next steps, tech debt, and session history live in `project_instructions.md`.
This file does not track state — it defines how to work.
