# MirAI School of Technology Capstone Mapping

## Project

**CareerCoach AI — Universal Interview Preparation and Salary Negotiation Workspace**

CareerCoach AI is a Streamlit and Gemini application for internship, placement, technical, behavioral, and compensation interview practice. It accepts any role description as text, optionally compares a resume with that role, generates topic-wise questions, provides an AI assistant, evaluates answers, ranks demonstrated skills, and links coding topics to external practice platforms.

## Evaluation matrix alignment

| Category | Max points | Evidence in this repository |
|---|---:|---|
| Technical implementation and architecture | 25 | Modular Python package, `st.session_state` for interview history and score persistence, `st.form` for setup and response submission, Pandas DataFrames for ranking and scorecards, defensive JSON parsing, deterministic fallbacks, and automated tests. |
| AI integration and prompt engineering | 20 | Gemini system instructions, dynamic f-string prompts, structured JSON schemas, role-specific context, resume-to-role matching, question-bank generation, answer evaluation, assistant chat, `st.camera_input`, and `st.audio_input`. |
| UI/UX and data visualization | 20 | Terminal-style dark dashboard, responsive `st.columns`, `st.expander` question cards, `st.metric` KPIs, Plotly radar/bar charts, `st.data_editor` skill ranking table, upload controls, navigation, and downloadable reports. |
| Deployment and cloud engineering | 15 | Streamlit Community Cloud configuration, public GitHub repository, `requirements.txt` without OS-level dependencies, Streamlit secrets guidance, and a live app link in the README. |
| Open-source branding | 10 | Customized README, project identity, setup instructions, architecture diagram, repository structure, testing commands, responsible-use note, and live deployment link. |
| System design and documentation | 10 | `docs/architecture.md` explains data flow, module boundaries, session-state design, API strategy, privacy behavior, fallback logic, and deployment assumptions. |

## Demonstration sequence

1. Open **Interview workspace** and type a target role plus internship description.
2. Select topics such as Behavioral, Technical, Projects, Coding, SQL, or System design.
3. Generate the question bank and show the KPI cards.
4. Ask the AI assistant for a mock question or explanation.
5. Answer a generated question and display the score, strengths, improvement points, model outline, and follow-up.
6. Complete two or more answers and show the demonstrated-skill ranking chart and editable data table.
7. Open the coding-practice links and show the role-specific coding focus.
8. Open **Role-fit practice**, upload a resume and role description, and show matched skills and gaps.
9. Open **Practice room** to demonstrate the original negotiation simulation and microphone input.

## Submission checklist

- [ ] GitHub repository is public and contains the latest `main` branch.
- [ ] Streamlit Community Cloud app is live and the URL is visible in `README.md`.
- [ ] `GEMINI_API_KEY` is configured in deployment secrets for live AI mode, or demo mode is shown clearly.
- [ ] `pytest -q` passes locally.
- [ ] `python -m compileall -q app.py modules tests` completes without errors.
- [ ] The final demo shows state persistence, form submission, AI response, KPI cards, charts, editable ranking table, and at least one multimodal control.
- [ ] No secrets, personal resumes, or internship documents are committed to Git.
