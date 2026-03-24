# BRD: Semantic SFX Curation Engine (v1.1)
**Project Codename:** Smart Sound Director

## 1. Executive Summary
The objective is to evolve the current SFX selection logic from a basic category-based randomization to a **Semantic Recommendation Engine**. This system will leverage LLM contextual awareness (Gemini) to request specific "traits" and use a weighted scoring algorithm to either fetch the best local match or trigger a high-fidelity generation via ElevenLabs API.

## 2. Strategic Objectives
- **Production Value:** Elevate short-form video quality through context-aware sound design.
- **Token Efficiency:** Minimize API round-trips by handling selection logic locally via Python.
- **Library Growth:** Use AI generation as a fallback to automatically expand the local asset library with tagged, high-quality resources.

## 3. Functional Requirements

### RF1: Multi-Tag Data Model (N:M Relationship)
The database must support a Many-to-Many relationship between `SFXAssets` and `Tags`.
- **Asset:** `id`, `file_path`, `usage_count`, `popularity_score`.
- **Tags:** `name` (e.g., "metallic", "echo", "sarcastic", "fast", "cartoon").

### RF2: Professional Director Schema (Gemini Output)
The JSON schema for script highlights must be expanded to include creative intent:
- **category:** Primary classification (e.g., "comedy").
- **desired_traits:** A list of strings describing the sound's texture/mood.
- **placement:** "start" or "end" of the segment.
- **beat_delay:** Enum `["none", "short", "long"]` to trigger dialogue pauses.
- **volume_modifier:** dB adjustment for final mixing.

### RF3: Semantic Scoring Algorithm (The "Quality Gate")
A Python service will rank local assets based on Gemini's request.

**Strict Quality Threshold:** If the best local match scores below **60/100**, the system must reject the local asset and trigger the ElevenLabs SFX API.

**Scoring Weights:**
- **Category Match (Mandatory):** 50%
- **Trait Intersection (Precision):** 40% (Calculated as matches / requested_tags).
- **LRU/Popularity (Variety):** 10%

**Critical Penalty:** Any asset matching less than 50% of requested traits is discarded to ensure variety and quality over convenience.

### RF4: "Beat & Pause" Synchronization
The audio assembly logic must calculate a "Comfort Gap" or "Beat" based on the selected SFX duration.

**Logic:** `next_dialogue_start = current_end + sfx_duration + beat_delay_constant`

## 4. Technical Constraints
- **RT1 (Asset Pre-processing):** All new/generated assets must be normalized to -6dB and capped at 3.0s duration before ingestion.
- **RT2 (Self-Learning Cache):** Sounds generated via API must be saved locally and automatically tagged with the `desired_traits` provided by Gemini to prevent redundant costs.
- **RT3 (Validation):** All data transfer objects (DTOs) must use Pydantic for strict type validation.

## 5. Scoring Example
**Input Request:** `category: "comedy"`, `traits: ["silly", "bonk", "cartoon", "squeaky", "fast"]` (5 traits).

- **Asset A (3/5 match):** Score ~74/100 → **ACCEPT** (Likely used if LRU allows).
- **Asset B (2/5 match):** Score ~46/100 → **REJECT** (Below 50% trait threshold) → Triggers API Generation.