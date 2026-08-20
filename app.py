from __future__ import annotations

import os
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from modules.ai_engine import AIEngine
from modules.document_parser import compact_text, extract_uploaded_text, file_label
from modules.report_generator import build_report
from modules.scoring import DIMENSIONS, best_and_worst, improvement_delta, normalize_scores, weighted_overall

st.set_page_config(page_title="CareerCoach AI", page_icon="CC", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root { --ink: #e9eef5; --muted: #9aa8b8; --line: #223044; --accent: #4ade80; --accent2: #60a5fa; }
.stApp { background: radial-gradient(circle at 80% 0%, #17253b 0, #0a101b 38%, #070b12 100%); color: var(--ink); }
section[data-testid="stSidebar"] { background: #0b121d; border-right: 1px solid var(--line); }
.block-container { max-width: 1250px; padding-top: 2rem; }
.hero { border: 1px solid #29415d; border-radius: 18px; padding: 2rem 2.2rem; background: linear-gradient(120deg, rgba(19,37,58,.92), rgba(10,17,29,.94)); box-shadow: 0 15px 45px rgba(0,0,0,.18); }
.kicker { color: var(--accent); font-family: monospace; letter-spacing: .12em; text-transform: uppercase; font-size: .78rem; }
.hero h1 { margin: .4rem 0 .55rem; font-size: 2.7rem; letter-spacing: -.04em; }
.hero p { color: #b8c5d4; max-width: 760px; font-size: 1.05rem; }
.panel { border: 1px solid var(--line); border-radius: 14px; padding: 1.2rem; background: rgba(13, 23, 37, .72); }
[data-testid="stMetricValue"] { color: var(--accent); }
.small-note { color: var(--muted); font-size: .86rem; }
div[data-testid="stForm"] { border: 1px solid var(--line); border-radius: 14px; padding: 1rem; background: rgba(13, 23, 37, .58); }
</style>
""", unsafe_allow_html=True)


def init_state() -> None:
    defaults = {
        "scenario": None,
        "transcript": [],
        "round_scores": [],
        "last_ai_response": "",
        "evaluation": None,
        "page": "Interview workspace",
        "match_context": None,
        "match_resume_name": "",
        "match_job_name": "",
        "practice_feedback": {},
        "interview_bank": None,
        "interview_role": "",
        "interview_context": "",
        "interview_description": "",
        "interview_candidate_context": "",
        "interview_topics": [],
        "assistant_history": [],
        "answer_evaluations": {},
        "provider": "demo",
        "provider_model": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    st.session_state.setdefault("provider_choice", "Grok")


def reset_session() -> None:
    for key in ["scenario", "transcript", "round_scores", "last_ai_response", "evaluation", "interview_bank", "interview_role", "interview_context", "interview_description", "interview_candidate_context", "interview_topics", "assistant_history", "answer_evaluations", "match_context", "practice_feedback"]:
        if key in ["scenario", "evaluation", "interview_bank", "match_context"]:
            st.session_state[key] = None
        elif key in ["transcript", "round_scores", "interview_topics", "assistant_history"]:
            st.session_state[key] = []
        elif key in ["answer_evaluations", "practice_feedback"]:
            st.session_state[key] = {}
        else:
            st.session_state[key] = ""


def scenario_form() -> None:
    st.subheader("Configure your negotiation scenario")
    with st.form("scenario_form"):
        first, second = st.columns(2)
        with first:
            role = st.text_input("Target role", "Software Engineering Intern")
            industry = st.selectbox("Industry", ["Technology", "FinTech", "EdTech", "Consulting", "Healthcare", "Other"])
            experience = st.selectbox("Experience level", ["Student / first internship", "Final-year student", "Recent graduate", "1–2 years experience"])
            work_mode = st.selectbox("Work arrangement", ["Hybrid", "On-site", "Remote"])
        with second:
            current_offer = st.number_input("Current offer (INR)", min_value=0.0, value=25000.0, step=1000.0)
            target_amount = st.number_input("Target amount (INR)", min_value=0.0, value=40000.0, step=1000.0)
            minimum_amount = st.number_input("Minimum acceptable amount (INR)", min_value=0.0, value=32000.0, step=1000.0)
            style = st.selectbox("Negotiation style", ["Evidence-led", "Collaborative", "Direct and concise", "Learning-focused"])
        submitted = st.form_submit_button("Start practice session", type="primary", use_container_width=True)
    if submitted:
        if minimum_amount > target_amount:
            st.error("Minimum acceptable amount cannot be higher than the target amount.")
            return
        st.session_state.scenario = {"role": role.strip() or "Software Engineering Intern", "industry": industry, "experience": experience, "work_mode": work_mode, "current_offer": current_offer, "target_amount": target_amount, "minimum_amount": minimum_amount, "style": style}
        st.session_state.transcript = []
        st.session_state.round_scores = []
        st.session_state.evaluation = None
        st.session_state.last_ai_response = "I am ready. Make your opening case for your target amount."
        st.rerun()


def role_fit_practice(engine: AIEngine) -> None:
    st.subheader("Resume-to-role practice")
    st.caption("Upload your resume and the internship description. CareerCoach will identify the match, surface gaps, and turn them into practice questions.")
    upload_left, upload_right = st.columns(2)
    with upload_left:
        resume_file = st.file_uploader("Upload resume", type=["pdf", "docx", "txt", "md", "csv"], key="resume_upload")
    with upload_right:
        job_file = st.file_uploader("Upload internship description", type=["pdf", "docx", "txt", "md", "csv"], key="job_upload")
    if resume_file and job_file and st.button("Analyze role fit", type="primary", use_container_width=True):
        try:
            resume_text = compact_text(extract_uploaded_text(resume_file))
            job_text = compact_text(extract_uploaded_text(job_file))
            if not resume_text or not job_text:
                st.error("Both files need readable text. Try a text-based PDF, DOCX, or TXT file.")
            else:
                with st.spinner("Comparing your resume with the internship requirements..."):
                    st.session_state.match_context = engine.match_resume_to_role(resume_text, job_text)
                st.session_state.match_resume_name = file_label(resume_file)
                st.session_state.match_job_name = file_label(job_file)
                st.session_state.practice_feedback = {}
                st.rerun()
        except ValueError as exc:
            st.error(str(exc))
    elif not (resume_file and job_file):
        st.info("Upload both documents to unlock personalized practice. Your files are read in memory for this session and are not stored by this app.")

    context = st.session_state.match_context
    if not context:
        return
    st.divider()
    st.markdown(f"**Resume:** `{st.session_state.match_resume_name}` &nbsp; · &nbsp; **Role description:** `{st.session_state.match_job_name}`")
    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("Role match", f"{context.get('match_score', 0)}/100")
    metric_b.metric("Matched skills", len(context.get("matched_skills", [])))
    metric_c.metric("Priority gaps", len(context.get("missing_skills", [])))
    st.write(context.get("role_summary", "Your personalized role-fit analysis is ready."))
    matched_col, gap_col = st.columns(2)
    with matched_col:
        st.markdown("#### Your evidence and matched skills")
        for item in context.get("matched_skills", []):
            st.write(f"✓ {item}")
        for item in context.get("evidence", []):
            st.caption(item)
    with gap_col:
        st.markdown("#### Skills to strengthen")
        for item in context.get("missing_skills", []):
            st.write(f"→ {item}")
    st.markdown("#### Practice questions")
    questions = context.get("questions", [])
    for index, item in enumerate(questions):
        question = item.get("question", "") if isinstance(item, dict) else str(item)
        with st.expander(f"{index + 1}. {question}", expanded=index == 0):
            if isinstance(item, dict):
                st.caption(item.get("why_it_matters", "Role-relevant question"))
                st.write("**Ideal points:** " + ", ".join(item.get("ideal_points", [])))
            answer_key = f"answer_{index}"
            answer = st.text_area("Your answer", key=answer_key, height=130, placeholder="Use Situation → Task → Action → Result. Include your own contribution.")
            if st.button("Get coaching feedback", key=f"coach_{index}"):
                if not answer.strip():
                    st.warning("Write an answer first so the coach can review it.")
                else:
                    with st.spinner("Reviewing your answer..."):
                        st.session_state.practice_feedback[index] = engine.coach_answer(context, question, answer)
            if index in st.session_state.practice_feedback:
                st.markdown(st.session_state.practice_feedback[index])
    with st.expander("Suggested preparation plan", expanded=False):
        for item in context.get("study_plan", []):
            st.write(f"• {item}")


def coding_practice_links(focus: list[str]) -> None:
    st.markdown("#### Coding practice platforms")
    st.caption("Use the generated focus areas to continue practice on an external coding platform.")
    links = {
        "LeetCode": ("Algorithms, data structures, SQL", "https://leetcode.com/problemset/"),
        "HackerRank": ("Interview preparation kits and SQL", "https://www.hackerrank.com/interview/preparation-kits"),
        "CodeSignal": ("Assessment-style coding practice", "https://app.codesignal.com/"),
        "GeeksforGeeks": ("Topic explanations and problems", "https://www.geeksforgeeks.org/explore"),
    }
    rows = [{"Platform": name, "Best for": purpose, "Open practice": url} for name, (purpose, url) in links.items()]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, column_config={"Open practice": st.column_config.LinkColumn("Open practice")})
    if focus:
        st.info("Suggested focus from the AI agent: " + ", ".join(focus))


def interview_workspace(engine: AIEngine) -> None:
    st.subheader("Universal interview practice")
    st.caption("Type any role or internship description. The AI assistant will generate questions, coach answers, and rank the skills you demonstrate.")
    with st.form("interview_setup_form"):
        role = st.text_input("Role or interview target", value=st.session_state.interview_role or "Software Engineering Intern")
        description = st.text_area("Role / internship description", placeholder="Paste the job description, required skills, responsibilities, or simply describe the interview you want to practise.", height=150)
        topics = st.multiselect("Topics to practise", ["Behavioral", "Technical", "Projects", "Role fit", "Teamwork", "Learning", "Coding", "SQL", "System design", "Communication"], default=["Behavioral", "Technical", "Projects", "Role fit"])
        candidate_context = st.text_area("Optional candidate context", placeholder="Add your experience, projects, resume summary, or strengths. This helps tailor the questions.", height=100)
        camera_snapshot = st.camera_input("Optional camera snapshot for visual practice", help="Capture a whiteboard, project sketch, or interview setup. The current demo records the input for the active session without persisting it.")
        generate = st.form_submit_button("Generate my interview practice plan", type="primary", use_container_width=True)
    if generate:
        if not role.strip() or not description.strip():
            st.error("Please enter both a role and a role or internship description.")
        else:
            with st.spinner("Building your personalized interview question bank..."):
                st.session_state.interview_bank = engine.generate_interview_bank(role.strip(), compact_text(description), topics, compact_text(candidate_context))
            st.session_state.interview_role = role.strip()
            st.session_state.interview_description = compact_text(description)
            st.session_state.interview_candidate_context = compact_text(candidate_context)
            st.session_state.interview_topics = topics
            camera_note = "A visual practice snapshot was provided." if camera_snapshot is not None else "No visual snapshot provided."
            st.session_state.interview_context = compact_text(
                f"ROLE TITLE: {role.strip()}\nSOURCE ROLE DESCRIPTION: {description}\nCANDIDATE CONTEXT: {candidate_context or 'Not provided'}\nVISUAL NOTE: {camera_note}"
            )
            st.session_state.assistant_history = []
            st.session_state.answer_evaluations = {}
            st.rerun()

    bank = st.session_state.interview_bank
    if not bank:
        st.info("Start by typing the role and the internship description above.")
        return
    st.divider()
    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("Questions generated", len(bank.get("questions", [])))
    metric_b.metric("Skills tracked", len(bank.get("skill_rubric", [])))
    metric_c.metric("Interview target", st.session_state.interview_role)
    st.write(bank.get("role_summary", "Your interview plan is ready."))
    assistant_col, practice_col = st.columns([0.8, 1.2])
    with assistant_col:
        st.markdown("#### AI interview assistant")
        for item in st.session_state.assistant_history:
            with st.chat_message("user" if item["speaker"] == "Candidate" else "assistant"):
                st.write(item["text"])
        with st.form("assistant_form", clear_on_submit=True):
            user_message = st.text_area("Ask for an explanation, hint, mock question, or study step", height=100)
            ask = st.form_submit_button("Ask assistant", type="primary", use_container_width=True)
        if ask and user_message.strip():
            st.session_state.assistant_history.append({"speaker": "Candidate", "text": user_message.strip()})
            with st.spinner("Assistant is thinking..."):
                answer = engine.interview_assistant(st.session_state.interview_role, st.session_state.interview_context, st.session_state.assistant_history, user_message.strip())
            st.session_state.assistant_history.append({"speaker": "Assistant", "text": answer})
            st.rerun()
    with practice_col:
        st.markdown("#### Question practice and skill ranking")
        questions = bank.get("questions", [])
        for index, item in enumerate(questions):
            question = item.get("question", "") if isinstance(item, dict) else str(item)
            label = f"{index + 1}. [{item.get('topic', 'Interview')}] {question}" if isinstance(item, dict) else f"{index + 1}. {question}"
            with st.expander(label, expanded=index == 0):
                if isinstance(item, dict):
                    st.caption(f"Difficulty: {item.get('difficulty', 'Intermediate')} · Ideal points: {', '.join(item.get('ideal_points', []))}")
                    if item.get("requirement_basis"):
                        st.info(f"Grounded in role requirement: {item['requirement_basis']}")
                answer_key = f"universal_answer_{index}"
                answer = st.text_area("Your answer", key=answer_key, height=120, placeholder="Answer with a real example. For behavioral questions use STAR; for technical questions explain assumptions, approach, and trade-offs.")
                if st.button("Evaluate answer", key=f"evaluate_universal_{index}"):
                    if not answer.strip():
                        st.warning("Write an answer first.")
                    else:
                        with st.spinner("Scoring your answer..."):
                            st.session_state.answer_evaluations[index] = engine.evaluate_interview_answer(st.session_state.interview_role, st.session_state.interview_context, question, answer, bank.get("skill_rubric", []))
                result = st.session_state.answer_evaluations.get(index)
                if result:
                    st.metric("Answer score", f"{float(result.get('score', 0)):.1f}/10")
                    st.write("**Requirement coverage:** " + result.get("requirement_addressed", "Connect your answer to the requirement named in the question."))
                    st.write("**Strengths:** " + " ".join(result.get("strengths", [])))
                    st.write("**Improve:** " + " ".join(result.get("improvements", [])))
                    st.write("**Model outline:** " + " → ".join(result.get("model_answer_outline", [])))
                    st.write("**Follow-up:** " + result.get("follow_up", "Add a measurable result."))
    if st.session_state.answer_evaluations:
        st.markdown("#### Your demonstrated skill rank")
        rank_scores = {}
        for result in st.session_state.answer_evaluations.values():
            for skill, score in result.get("skill_scores", {}).items():
                rank_scores.setdefault(skill, []).append(float(score))
        ranked = sorted(((skill, sum(values) / len(values)) for skill, values in rank_scores.items()), key=lambda row: row[1], reverse=True)
        if ranked:
            rank_df = pd.DataFrame(ranked, columns=["Skill", "Score"])
            st.plotly_chart(px.bar(rank_df, x="Score", y="Skill", orientation="h", range_x=[0, 10], template="plotly_dark", color="Score", color_continuous_scale="Teal"), use_container_width=True)
            st.data_editor(rank_df, use_container_width=True, hide_index=True, disabled=True, key="skill_rank_editor")
    coding_practice_links(bank.get("coding_focus", []))


def practice_room(engine: AIEngine) -> None:
    if not st.session_state.scenario:
        scenario_form()
        return
    scenario = st.session_state.scenario
    st.subheader("Practice room")
    st.caption(f"{scenario['role']} · {scenario['industry']} · {scenario['experience']} · {scenario['style']}")
    left, right = st.columns([1.35, .65])
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        if not st.session_state.transcript:
            st.info("The HR manager is waiting for your opening statement. Explain the value you bring and your target amount.")
        for item in st.session_state.transcript:
            with st.chat_message("user" if item["speaker"] == "Candidate" else "assistant"):
                st.write(item["text"])
        st.markdown('</div>', unsafe_allow_html=True)
        with st.form("response_form", clear_on_submit=True):
            mode = st.radio("Response mode", ["Text", "Voice recording"], horizontal=True)
            response = st.text_area("Your response", placeholder="Example: In my recent project, I reduced...", height=120) if mode == "Text" else ""
            audio = st.audio_input("Record your response") if mode == "Voice recording" else None
            submitted = st.form_submit_button("Send response", type="primary")
        if submitted:
            if audio is not None and not response:
                st.warning("Audio was recorded. Add a transcript in the text box next time, or use text mode for this demo build.")
            if response.strip():
                st.session_state.transcript.append({"speaker": "Candidate", "text": response.strip()})
                with st.spinner("CareerCoach AI is responding..."):
                    ai_text = engine.hr_response(scenario, st.session_state.transcript)
                st.session_state.transcript.append({"speaker": "HR Manager", "text": ai_text})
                st.session_state.last_ai_response = ai_text
                st.rerun()
    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("#### Scenario snapshot")
        st.metric("Current offer", f"INR {scenario['current_offer']:,.0f}")
        st.metric("Target amount", f"INR {scenario['target_amount']:,.0f}")
        st.metric("Rounds completed", str(sum(1 for item in st.session_state.transcript if item["speaker"] == "Candidate")))
        st.markdown("#### Quick framework")
        st.write("**Value → Target → Flexibility**")
        st.caption("Connect your request to evidence, state a clear target, then show that you can discuss the total package.")
        if st.button("End and evaluate session", use_container_width=True, disabled=not st.session_state.transcript):
            with st.spinner("Building your scorecard..."):
                st.session_state.evaluation = engine.evaluate(scenario, st.session_state.transcript)
            st.session_state.page = "Results dashboard"
            st.rerun()
        if st.button("Reset scenario", use_container_width=True):
            reset_session()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def results_dashboard() -> None:
    evaluation = st.session_state.evaluation
    if not evaluation:
        st.info("Complete a practice session to unlock the results dashboard.")
        return
    scores = normalize_scores(evaluation.get("scores"))
    overall = weighted_overall(scores)
    best, worst = best_and_worst(scores)
    st.subheader("Results dashboard")
    st.write(evaluation.get("summary", "Your evaluation is ready."))
    a, b, c, d = st.columns(4)
    a.metric("Overall score", f"{overall:.1f}/10", delta=f"{improvement_delta(st.session_state.round_scores):+.1f} vs first round" if st.session_state.round_scores else None)
    b.metric("Strongest skill", best)
    c.metric("Focus area", worst)
    d.metric("Rounds reviewed", sum(1 for item in st.session_state.transcript if item["speaker"] == "Candidate"))
    chart_left, chart_right = st.columns(2)
    score_df = pd.DataFrame({"Dimension": DIMENSIONS, "Score": [scores[d] for d in DIMENSIONS]})
    with chart_left:
        st.plotly_chart(px.line_polar(score_df, r="Score", theta="Dimension", line_close=True, range_r=[0, 10], template="plotly_dark", title="Negotiation skill profile"), use_container_width=True)
    with chart_right:
        st.plotly_chart(px.bar(score_df, x="Score", y="Dimension", orientation="h", range_x=[0, 10], template="plotly_dark", title="Dimension scorecard", color="Score", color_continuous_scale="Teal"), use_container_width=True)
    st.divider()
    for title, key in [("Strengths", "strengths"), ("Development areas", "weaknesses"), ("Missed opportunities", "missed_opportunities"), ("Recommended phrases", "recommended_phrases"), ("Seven-day practice plan", "seven_day_plan")]:
        with st.expander(title, expanded=title in ["Strengths", "Development areas"]):
            for item in evaluation.get(key, []):
                st.write(f"• {item}")
    report = build_report(st.session_state.scenario, evaluation, st.session_state.transcript)
    st.download_button("Download coaching report", report, file_name="careercoach_report.md", mime="text/markdown", type="primary")


def provider_controls() -> AIEngine:
    """Read provider settings from ephemeral UI state, environment, or Streamlit secrets."""
    def secret_or_env(name: str) -> str:
        try:
            return str(st.secrets.get(name, "") or os.getenv(name, "")).strip()
        except Exception:
            return os.getenv(name, "").strip()

    st.sidebar.markdown("**AI provider**")
    provider = st.sidebar.selectbox("Choose engine", ["Grok", "Demo mode"], key="provider_choice")
    provider_key = {"Demo mode": "demo", "Grok": "grok"}[provider]
    default_key = secret_or_env("GROK_API_KEY")
    api_key = st.sidebar.text_input("Grok API key (optional)", value=default_key, type="password", help="Stored only in this active Streamlit session unless you configure it in Secrets.") if provider_key == "grok" else ""
    default_model = secret_or_env("GROK_MODEL")
    model = st.sidebar.text_input("Model (optional)", value=default_model, placeholder="Use the provider default") if provider_key != "demo" else "demo"
    st.session_state.provider = provider_key
    st.session_state.provider_model = model

    engine = AIEngine(provider_key, api_key, model)
    if engine.available:
        st.sidebar.success(f"{engine.label} connected")
    elif provider_key == "demo":
        st.sidebar.info("Demo mode active — no API key needed")
    else:
        st.sidebar.warning(f"{engine.label} key not configured — local fallback will be used")
    return engine


def main() -> None:
    init_state()
    engine = provider_controls()
    with st.sidebar:
        st.markdown("## `careercoach_ai`")
        st.caption("Voice-driven negotiation practice")
        pages = ["Practice room", "Interview workspace", "Role-fit practice", "Results dashboard"]
        st.session_state.page = st.radio("Navigate", pages, index=pages.index(st.session_state.page) if st.session_state.page in pages else 0)
        st.divider()
        st.markdown("**Engine status**")
        st.write(f"Provider: **{engine.label}**")
        st.caption("Grok is the live provider. Demo mode is available only as a local fallback when no key is configured.")
        if getattr(engine, "last_error", ""):
            st.error(f"Grok request issue: {engine.last_error}")
        if st.button("Start a fresh session", use_container_width=True):
            reset_session()
            st.session_state.interview_bank = None
            st.session_state.assistant_history = []
            st.session_state.answer_evaluations = {}
            st.rerun()
    st.markdown('<div class="hero"><div class="kicker">// grok-grounded interview lab</div><h1>CareerCoach AI</h1><p>Paste the role description, connect Grok, and practise against the actual requirements—not a generic interview script.</p></div>', unsafe_allow_html=True)
    st.write("")
    if st.session_state.page == "Practice room":
        practice_room(engine)
    elif st.session_state.page == "Interview workspace":
        interview_workspace(engine)
    elif st.session_state.page == "Role-fit practice":
        role_fit_practice(engine)
    else:
        results_dashboard()


if __name__ == "__main__":
    main()
