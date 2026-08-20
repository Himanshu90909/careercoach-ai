# Technical Design Document

## System purpose

CareerCoach AI provides a guided negotiation practice experience. The application collects a structured scenario, maintains the conversation in memory, asks Gemini to role-play an HR manager, and evaluates the completed transcript.

## Data flow

1. The user submits the scenario form. The form validates the compensation boundaries before storing the scenario in Streamlit session state.
2. The user submits a text response or records audio through `st.audio_input`. Text is the current analysis input; the voice path is intentionally visible and provides a graceful fallback when transcription is not configured.
3. The prompt builder injects only the scenario context and recent transcript into the HR prompt.
4. The AI engine calls Gemini when `GEMINI_API_KEY` is available. If it is absent or a request fails, deterministic demo responses keep the product usable.
5. At the end of the session, the evaluation prompt requests a strict JSON scorecard. The parser extracts JSON defensively and falls back to a local evaluation object if parsing fails.
6. The scoring module normalises each dimension and calculates the weighted overall score locally, ensuring that dashboard totals are reproducible.
7. Plotly charts and the Markdown report use the same scorecard and transcript stored in session state.

## Module responsibilities

| Module | Responsibility |
|---|---|
| `app.py` | Presentation layer, navigation, forms, state transitions, charts, and downloads |
| `modules/prompts.py` | Prompt construction and dynamic scenario context |
| `modules/ai_engine.py` | Gemini client, model calls, JSON parsing, and demo fallback behaviour |
| `modules/scoring.py` | Score clamping, weighted scoring, best/worst dimensions, and deltas |
| `modules/report_generator.py` | Human-readable Markdown report generation |

## Security and reliability

The Gemini key is read from an environment variable and is never embedded in source code. Streamlit secrets are recommended for deployment. API failures are caught at the AI boundary, while score calculations remain local and deterministic. The app does not persist personal data beyond the active browser session.

## Known limitation

The interface includes a microphone recorder, but production-grade speech-to-text is not bundled in this first version because it would add another external service and deployment credential. The application presents a clear text fallback. A future iteration can add Gemini audio transcription or a dedicated speech-to-text provider behind the same `AIEngine` interface.
