# CareerCoach AI

> `careercoach_ai :: voice-driven salary negotiation simulator`

CareerCoach AI is a general interview-preparation workspace built with Streamlit and Gemini. It accepts any role or internship description as text, can compare a resume with the role, generates topic-wise interview questions, provides an AI interview assistant, evaluates written answers, ranks demonstrated skills, and links candidates to external coding-practice platforms.

## Why this project exists

Students often know their technical skills but have not rehearsed how to communicate value, justify a target amount, or respond to a constrained offer. CareerCoach AI turns that difficult conversation into a repeatable practice loop: configure a scenario, negotiate, review the scorecard, and practise again.

## Features

The application provides three preparation paths: a salary negotiation room, a universal **Interview workspace** with text-based role setup, and a **Role-fit practice** page for resume and internship-description uploads. The interview workspace generates behavioral, technical, project, role-fit, teamwork, learning, coding, SQL, system-design, and communication questions; supports an AI assistant chat; evaluates written answers; visualizes demonstrated skill ranks; and recommends LeetCode, HackerRank, CodeSignal, and GeeksforGeeks practice. Deterministic fallbacks keep the workflow usable without an API key.

## Architecture

```mermaid
flowchart TD
    UI[Streamlit UI] --> FORM[Scenario Form]
    FORM --> STATE[Session State]
    STATE --> INPUT[Text or Audio Input]
    UPLOAD[Resume + Internship Description] --> PARSE[In-memory Document Parser]
    PARSE --> MATCH[Gemini Role Match + Question Plan]
    MATCH --> ROLEFIT[Role-fit Practice]
    TEXTROLE[Typed role + description] --> BANK[Question Bank]
    BANK --> ASSIST[AI Interview Assistant]
    BANK --> ANSWERS[Answer Evaluation]
    ANSWERS --> RANK[Skill Ranking]
    BANK --> CODING[External Coding Practice Links]
    INPUT --> PROMPT[Prompt Builder]
    PROMPT --> GEMINI[Gemini API]
    GEMINI --> TRANSCRIPT[Conversation History]
    TRANSCRIPT --> EVAL[Structured Evaluation]
    EVAL --> SCORE[Local Weighted Scoring]
    SCORE --> DASH[Dashboard and Report]
```

## Run locally

```bash
git clone <your-repository-url>
cd careercoach-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app starts in **demo mode** if `GEMINI_API_KEY` is absent. To enable live Gemini responses, create `.streamlit/secrets.toml` locally:

```toml
GEMINI_API_KEY = "your-key-here"
```

Never commit that file. The included `.gitignore` excludes it.

## Deploy to Streamlit Community Cloud

Create a new app from the GitHub repository, set the main file to `app.py`, and add the following secret in the app settings:

```toml
GEMINI_API_KEY = "your-key-here"
```

The project uses only Python packages declared in `requirements.txt` and does not require local system dependencies.

## Project structure

| Path | Responsibility |
|---|---|
| `app.py` | Streamlit UI, navigation, session state, charts, and interaction flow |
| `modules/ai_engine.py` | Gemini client, question generation, assistant chat, answer scoring, role matching, coaching, and demo fallbacks |
| `modules/prompts.py` | Dynamic negotiation, role-matching, question-bank, assistant, and answer-evaluation prompts |
| `modules/document_parser.py` | In-memory PDF, DOCX, TXT, Markdown, and CSV text extraction |
| `modules/scoring.py` | Deterministic score normalisation and weighted scoring |
| `modules/report_generator.py` | Downloadable Markdown report generation |
| `tests/` | Unit tests for scoring, parsing, and role matching |
| `docs/architecture.md` | Technical design and data-flow explanation |

## Evaluation rubric coverage

| Requirement | Implementation |
|---|---|
| Streamlit forms and session state | Scenario setup uses `st.form`; active conversation is preserved in `st.session_state` |
| Gemini integration | Role-specific HR, evaluation, role-match, question generation, assistant, and answer-coaching prompts |
| Multimodality | Typed role descriptions, resume/job-document uploads, and `st.audio_input` voice practice with a text fallback |
| Data visualisation | KPI cards, radar profile, horizontal scorecards, answer scores, and demonstrated-skill ranking |
| Deployment | Streamlit Community Cloud-compatible requirements |
| Open-source branding | Terminal-style title, architecture diagram, setup instructions, and documented modules |

## Testing

```bash
pytest -q
python -m py_compile app.py modules/*.py
```

## Responsible-use note

This is an educational practice tool. Its salary values and feedback are simulated and should not be treated as financial, legal, or employment advice.
