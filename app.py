from __future__ import annotations

import os
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules.ai_engine import AIEngine
from modules.document_parser import compact_text, extract_uploaded_text, file_label
from modules.progress import (
    ACHIEVEMENT_BADGES,
    INTERVIEW_TIPS,
    NEGOTIATION_TIPS,
    QUICK_START_TEMPLATES,
    all_badges,
    score_verdict,
)
from modules.report_generator import build_report
from modules.scoring import DIMENSIONS, best_and_worst, improvement_delta, normalize_scores, weighted_overall

st.set_page_config(page_title="CareerCoach AI", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

# ──────────────────────────────────────────────────────────────────────────────
# STYLES
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
  --ink: #e9eef5;
  --muted: #9aa8b8;
  --line: #223044;
  --accent: #4ade80;
  --accent2: #60a5fa;
  --accent3: #fbbf24;
  --accent4: #a78bfa;
  --bg: #0a101b;
  --bg2: #0d1725;
  --card: rgba(19, 37, 58, 0.72);
  --card-hover: rgba(29, 47, 68, 0.88);
}

.stApp {
  background: radial-gradient(circle at 80% 0%, #17253b 0%, #0a101b 38%, #070b12 100%);
  color: var(--ink);
}
section[data-testid="stSidebar"] {
  background: #0b121d;
  border-right: 1px solid var(--line);
}
.block-container { max-width: 1250px; padding-top: 1.5rem; }

/* Hero */
.hero {
  border: 1px solid #29415d;
  border-radius: 18px;
  padding: 2.5rem 2.5rem;
  background: linear-gradient(120deg, rgba(19,37,58,.92), rgba(10,17,29,.94));
  box-shadow: 0 15px 45px rgba(0,0,0,.18);
  position: relative;
  overflow: hidden;
}
.hero::before {
  content: '';
  position: absolute;
  top: -40%;
  right: -8%;
  width: 320px;
  height: 320px;
  background: radial-gradient(circle, rgba(74,222,128,.08) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}
.hero h1 {
  margin: .3rem 0 .5rem;
  font-size: 2.8rem;
  letter-spacing: -.04em;
  background: linear-gradient(135deg, #4ade80 0%, #60a5fa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero p { color: #b8c5d4; max-width: 720px; font-size: 1.06rem; }
.kicker {
  color: var(--accent);
  font-family: monospace;
  letter-spacing: .12em;
  text-transform: uppercase;
  font-size: .76rem;
  margin-bottom: .3rem;
}

/* Cards */
.cc-card {
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 1.4rem 1.5rem;
  background: var(--card);
  transition: border-color .25s ease, background .25s ease, transform .2s ease, box-shadow .25s ease;
  height: 100%;
}
.cc-card:hover {
  background: var(--card-hover);
  border-color: var(--accent);
  transform: translateY(-3px);
  box-shadow: 0 10px 30px rgba(74, 222, 128, .08);
}
.cc-card-title { font-size: 1.05rem; font-weight: 600; margin: .3rem 0 .15rem; color: var(--ink); }
.cc-card-sub { font-size: .84rem; color: var(--muted); }

/* Tag */
.cc-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: .7rem;
  font-weight: 600;
  letter-spacing: .04em;
  text-transform: uppercase;
}

/* Panel */
.panel {
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 1.2rem;
  background: rgba(13, 23, 37, .72);
}

/* Badge */
.cc-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 10px;
  border: 1px solid var(--line);
  background: rgba(13, 23, 37, .5);
  font-size: .82rem;
  color: var(--muted);
}
.cc-badge.earned {
  border-color: var(--accent3);
  background: rgba(251, 191, 36, .08);
  color: var(--accent3);
}

/* Tip card */
.tip-card {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 1rem 1.2rem;
  background: rgba(13, 23, 37, .5);
  transition: border-color .2s ease, background .2s ease;
}
.tip-card:hover {
  border-color: var(--accent2);
  background: rgba(13, 23, 37, .7);
}
.tip-icon { font-size: 1.4rem; }
.tip-title { font-weight: 600; margin: .2rem 0 .3rem; }
.tip-body { font-size: .87rem; color: var(--muted); line-height: 1.5; }

/* Score verdict */
.score-verdict {
  padding: 1rem 1.5rem;
  border-radius: 12px;
  text-align: center;
  font-size: 1.1rem;
  font-weight: 600;
}

/* Progress bar */
.cc-progress {
  height: 6px;
  border-radius: 3px;
  background: var(--line);
  overflow: hidden;
  margin-top: .3rem;
}
.cc-progress-fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  transition: width .5s ease;
}

/* Metric values */
[data-testid="stMetricValue"] { color: var(--accent); }
[data-testid="stMetricLabel"] { font-size: .8rem; }
.small-note { color: var(--muted); font-size: .86rem; }

/* Form */
div[data-testid="stForm"] {
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 1rem;
  background: rgba(13, 23, 37, .58);
}

/* Feature icon */
.feature-icon { font-size: 2rem; }

/* Fade-in */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.fade-in { animation: fadeIn .4s ease-out; }

/* StTab styling */
.stTabs [data-baseline-content-type] button {
  font-weight: 500;
}

/* Button focus */
.stButton > button:hover {
  border-color: var(--accent) !important;
}

/* Divider custom */
.cc-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--line), transparent);
  margin: 1.5rem 0;
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# STATE
# ──────────────────────────────────────────────────────────────────────────────
def init_state() -> None:
    defaults = {
        "scenario": None,
        "transcript": [],
        "round_scores": [],
        "last_ai_response": "",
        "evaluation": None,
        "page": "Home",
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
        # Progress tracking
        "session_count": 0,
        "best_score": 0.0,
        "modes_used": set(),
        "session_history": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    st.session_state.setdefault("provider_choice", "Grok")


def reset_session() -> None:
    for key in ["scenario", "transcript", "round_scores", "last_ai_response", "evaluation",
                "interview_bank", "interview_role", "interview_context", "interview_description",
                "interview_candidate_context", "interview_topics", "assistant_history",
                "answer_evaluations", "match_context", "practice_feedback"]:
        if key in ["scenario", "evaluation", "interview_bank", "match_context"]:
            st.session_state[key] = None
        elif key in ["transcript", "round_scores", "interview_topics", "assistant_history"]:
            st.session_state[key] = []
        elif key in ["answer_evaluations", "practice_feedback"]:
            st.session_state[key] = {}
        else:
            st.session_state[key] = ""


def record_session(mode: str, score: float) -> None:
    """Track a completed practice session for progress / achievements."""
    st.session_state.session_count += 1
    st.session_state.best_score = max(st.session_state.best_score, score)
    st.session_state.modes_used.add(mode)
    st.session_state.session_history.append({"mode": mode, "score": score})


# ──────────────────────────────────────────────────────────────────────────────
# LANDING PAGE
# ──────────────────────────────────────────────────────────────────────────────
def landing_page(engine: AIEngine) -> None:
    # Hero
    st.markdown("""
    <div class="hero fade-in">
      <div class="kicker">// your AI-powered interview & negotiation coach</div>
      <h1>CareerCoach AI</h1>
      <p>Practice salary negotiations, ace role-specific interviews, and get instant coaching —
         grounded in the actual job description, not a generic template.</p>
    </div>
    """, unsafe_allow_html=True)
    st.write("")

    # Progress overview
    sc = st.session_state.session_count
    bs = st.session_state.best_score
    mu = st.session_state.modes_used
    if sc > 0:
        m1, m2, m3 = st.columns(3)
        m1.metric("Sessions completed", str(sc))
        m2.metric("Best score", f"{bs:.1f}/10")
        m3.metric("Modes tried", f"{len(mu)}/3")

        earned = all_badges(sc, bs, mu)
        earned_count = sum(1 for b in earned if b["earned"])
        st.markdown(f"**Achievements** &nbsp; <span class='small-note'>{earned_count}/{len(earned)} unlocked</span>", unsafe_allow_html=True)
        badge_cols = st.columns(len(earned))
        for col, badge in zip(badge_cols, earned):
            cls = "cc-badge earned" if badge["earned"] else "cc-badge"
            col.markdown(
                f"<div class='{cls}'>{badge['emoji']} {badge['name']}</div>",
                unsafe_allow_html=True,
            )
        st.markdown("")

    # Feature cards
    st.markdown("### What would you like to practice?")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("""
        <div class="cc-card">
          <div class="feature-icon">💬</div>
          <div class="cc-card-title">Negotiation Practice</div>
          <div class="cc-card-sub">Simulate a salary negotiation with an AI HR manager. Get a detailed scorecard on your performance.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start negotiating", key="go_negotiate", use_container_width=True, type="primary"):
            st.session_state.page = "Practice room"
            st.rerun()
    with f2:
        st.markdown("""
        <div class="cc-card">
          <div class="feature-icon">📋</div>
          <div class="cc-card-title">Interview Prep</div>
          <div class="cc-card-sub">Paste a job description and get role-specific questions, coaching, and skill ranking — grounded in real requirements.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Prep for interviews", key="go_interview", use_container_width=True, type="primary"):
            st.session_state.page = "Interview workspace"
            st.rerun()
    with f3:
        st.markdown("""
        <div class="cc-card">
          <div class="feature-icon">📄</div>
          <div class="cc-card-title">Role-Fit Analysis</div>
          <div class="cc-card-sub">Upload your resume + job description. See your match score, skill gaps, and get personalized practice questions.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Check role fit", key="go_rolfit", use_container_width=True, type="primary"):
            st.session_state.page = "Role-fit practice"
            st.rerun()

    st.markdown("")

    # Quick-start templates
    st.markdown("### ⚡ Quick start — jump into a scenario")
    st.caption("One-click templates. No setup required.")
    qs_cols = st.columns(len(QUICK_START_TEMPLATES))
    for col, template in zip(qs_cols, QUICK_START_TEMPLATES):
        with col:
            tag_html = f"<span class='cc-tag' style='color:{template['tag_color']}; border:1px solid {template['tag_color']}33; background:{template['tag_color']}11'>{template['tag']}</span>"
            st.markdown(
                f"<div class='cc-card'>"
                f"<div>{tag_html}</div>"
                f"<div class='cc-card-title' style='margin-top:.5rem'>{template['title']}</div>"
                f"<div class='cc-card-sub'>{template['subtitle']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if st.button(f"Start", key=f"qs_{template['title']}", use_container_width=True):
                st.session_state.scenario = template["scenario"]
                st.session_state.transcript = []
                st.session_state.round_scores = []
                st.session_state.evaluation = None
                st.session_state.last_ai_response = "I am ready. Make your opening case for your target amount."
                st.session_state.page = "Practice room"
                st.rerun()

    st.markdown("")

    # Tips preview
    st.markdown("### 💡 Quick tips before you start")
    t1, t2, t3 = st.columns(3)
    tips_combined = NEGOTIATION_TIPS[:3] + INTERVIEW_TIPS[:3]
    for col, tip in zip([t1, t2, t3], tips_combined[:3]):
        col.markdown(
            f"<div class='tip-card'>"
            f"<div class='tip-icon'>{tip['icon']}</div>"
            f"<div class='tip-title'>{tip['title']}</div>"
            f"<div class='tip-body'>{tip['tip']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    if st.button("See all tips & resources", key="go_tips", use_container_width=True):
        st.session_state.page = "Tips & Resources"
        st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# SCENARIO FORM
# ──────────────────────────────────────────────────────────────────────────────
def scenario_form() -> None:
    st.subheader("Configure your negotiation scenario")
    st.caption("Fill in the details, or go back to the Home page to use a quick-start template.")
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
        st.session_state.scenario = {
            "role": role.strip() or "Software Engineering Intern",
            "industry": industry,
            "experience": experience,
            "work_mode": work_mode,
            "current_offer": current_offer,
            "target_amount": target_amount,
            "minimum_amount": minimum_amount,
            "style": style,
        }
        st.session_state.transcript = []
        st.session_state.round_scores = []
        st.session_state.evaluation = None
        st.session_state.last_ai_response = "I am ready. Make your opening case for your target amount."
        st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# ROLE-FIT PRACTICE
# ──────────────────────────────────────────────────────────────────────────────
def role_fit_practice(engine: AIEngine) -> None:
    st.subheader("Resume-to-role practice")
    st.caption("Upload your resume and the internship description. CareerCoach identifies the match, surfaces gaps, and turns them into practice questions.")
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
                st.session_state.modes_used.add("role-fit")
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

    # Match score with progress bar
    match_score = context.get("match_score", 0)
    score_color = "#4ade80" if match_score >= 70 else "#fbbf24" if match_score >= 40 else "#f87171"
    m_a, m_b, m_c = st.columns(3)
    m_a.metric("Role match", f"{match_score}/100")
    m_b.metric("Matched skills", len(context.get("matched_skills", [])))
    m_c.metric("Priority gaps", len(context.get("missing_skills", [])))
    st.markdown(
        f"<div class='cc-progress'><div class='cc-progress-fill' style='width:{match_score}%; background:linear-gradient(90deg, {score_color}, {score_color}cc)'></div></div>",
        unsafe_allow_html=True,
    )
    st.caption("Role match score")

    st.write(context.get("role_summary", "Your personalized role-fit analysis is ready."))
    matched_col, gap_col = st.columns(2)
    with matched_col:
        st.markdown("#### ✓ Your evidence and matched skills")
        for item in context.get("matched_skills", []):
            st.write(f"✓ {item}")
        for item in context.get("evidence", []):
            st.caption(item)
    with gap_col:
        st.markdown("#### → Skills to strengthen")
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
                feedback = st.session_state.practice_feedback[index]
                st.markdown(f"<div class='panel' style='margin-top:.5rem'>{feedback}</div>", unsafe_allow_html=True)
    with st.expander("Suggested preparation plan", expanded=False):
        for item in context.get("study_plan", []):
            st.write(f"• {item}")


# ──────────────────────────────────────────────────────────────────────────────
# CODING PRACTICE LINKS
# ──────────────────────────────────────────────────────────────────────────────
def coding_practice_links(focus: list[str]) -> None:
    st.markdown("#### Coding practice platforms")
    st.caption("Use the generated focus areas to continue practice on an external coding platform.")
    links = {
        "LeetCode": ("Algorithms, data structures, SQL", "https://leetcode.com/problemset/"),
        "HackerRank": ("Interview preparation kits and SQL", "https://www.hackerrank.com/interview/preparation-kits"),
        "CodeSignal": ("Assessment-style coding practice", "https://app.codesignal.com/"),
        "Pramp": ("Live peer-to-peer mock interviews", "https://www.pramp.com/"),
    }
    rows = [{"Platform": name, "Best for": purpose, "Open practice": url} for name, (purpose, url) in links.items()]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, column_config={"Open practice": st.column_config.LinkColumn("Open practice")})
    if focus:
        st.info("Suggested focus from the AI agent: " + ", ".join(focus))


# ──────────────────────────────────────────────────────────────────────────────
# INTERVIEW WORKSPACE
# ──────────────────────────────────────────────────────────────────────────────
def interview_workspace(engine: AIEngine) -> None:
    st.subheader("Universal interview practice")
    st.caption("Type any role or internship description. The AI generates questions, coaches answers, and ranks the skills you demonstrate.")

    with st.form("interview_setup_form"):
        role = st.text_input("Role or interview target", value=st.session_state.interview_role or "Software Engineering Intern")
        description = st.text_area("Role / internship description", placeholder="Paste the job description, required skills, responsibilities, or describe the interview you want to practise.", height=150)
        topics = st.multiselect("Topics to practise", ["Behavioral", "Technical", "Projects", "Role fit", "Teamwork", "Learning", "Coding", "SQL", "System design", "Communication"], default=["Behavioral", "Technical", "Projects", "Role fit"])
        candidate_context = st.text_area("Optional candidate context", placeholder="Add your experience, projects, resume summary, or strengths. This helps tailor the questions.", height=100)
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
            st.session_state.interview_context = compact_text(
                f"ROLE TITLE: {role.strip()}\nSOURCE ROLE DESCRIPTION: {description}\nCANDIDATE CONTEXT: {candidate_context or 'Not provided'}"
            )
            st.session_state.assistant_history = []
            st.session_state.answer_evaluations = {}
            st.session_state.modes_used.add("interview")
            st.rerun()

    bank = st.session_state.interview_bank
    if not bank:
        st.info("Start by typing the role and the internship description above.")
        return
    st.divider()

    total_q = len(bank.get("questions", []))
    answered = len(st.session_state.answer_evaluations)
    m_a, m_b, m_c = st.columns(3)
    m_a.metric("Questions generated", total_q)
    m_b.metric("Skills tracked", len(bank.get("skill_rubric", [])))
    m_c.metric("Questions answered", f"{answered}/{total_q}")

    if total_q > 0:
        progress_pct = int((answered / total_q) * 100)
        st.markdown(
            f"<div class='cc-progress'><div class='cc-progress-fill' style='width:{progress_pct}%'></div></div>",
            unsafe_allow_html=True,
        )
        st.caption(f"Practice progress: {progress_pct}%")

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
                        st.rerun()
                result = st.session_state.answer_evaluations.get(index)
                if result:
                    ans_score = float(result.get("score", 0))
                    verdict, msg = score_verdict(ans_score)
                    verdict_color = "#4ade80" if ans_score >= 7 else "#fbbf24" if ans_score >= 5 else "#f87171"
                    st.markdown(
                        f"<div class='score-verdict' style='background:{verdict_color}22; color:{verdict_color}; border:1px solid {verdict_color}44'>"
                        f"Score: {ans_score:.1f}/10 — {verdict}</div>",
                        unsafe_allow_html=True,
                    )
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
            rank_df = pd.DataFrame(ranked, columns=["Skill", "Average Score"])
            st.plotly_chart(px.bar(rank_df, x="Average Score", y="Skill", orientation="h", range_x=[0, 10], template="plotly_dark", color="Average Score", color_continuous_scale="Teal"), use_container_width=True)
            st.data_editor(rank_df, use_container_width=True, hide_index=True, disabled=True, key="skill_rank_editor")
    coding_practice_links(bank.get("coding_focus", []))

    if answered > 0:
        if st.button("Finish interview session", type="primary", use_container_width=True):
            avg_score = sum(float(r.get("score", 0)) for r in st.session_state.answer_evaluations.values()) / max(1, len(st.session_state.answer_evaluations))
            record_session("interview", avg_score)
            st.balloons()
            st.success(f"Session complete! Average answer score: {avg_score:.1f}/10. Check the Home page for your updated achievements.")


# ──────────────────────────────────────────────────────────────────────────────
# PRACTICE ROOM
# ──────────────────────────────────────────────────────────────────────────────
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
            response = st.text_area("Your response", placeholder="Example: In my recent project, I reduced...", height=120)
            submitted = st.form_submit_button("Send response", type="primary")
        if submitted:
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
        rounds = sum(1 for item in st.session_state.transcript if item["speaker"] == "Candidate")
        st.metric("Rounds completed", str(rounds))

        # Progress indicator
        if rounds > 0:
            progress_pct = min(100, rounds * 25)
            st.markdown(
                f"<div class='cc-progress'><div class='cc-progress-fill' style='width:{progress_pct}%'></div></div>",
                unsafe_allow_html=True,
            )
            st.caption("Practice depth")

        st.markdown("#### Quick framework")
        st.write("**Value → Target → Flexibility**")
        st.caption("Connect your request to evidence, state a clear target, then show you can discuss the total package.")
        if st.button("End and evaluate session", use_container_width=True, disabled=not st.session_state.transcript):
            with st.spinner("Building your scorecard..."):
                st.session_state.evaluation = engine.evaluate(scenario, st.session_state.transcript)
            st.session_state.page = "Results dashboard"
            st.rerun()
        if st.button("Reset scenario", use_container_width=True):
            reset_session()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# RESULTS DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────
def results_dashboard() -> None:
    evaluation = st.session_state.evaluation
    if not evaluation:
        st.info("Complete a practice session to unlock the results dashboard.")
        return
    scores = normalize_scores(evaluation.get("scores"))
    overall = weighted_overall(scores)
    best, worst = best_and_worst(scores)

    # Record the session on first view
    if not st.session_state.get("_eval_recorded", False):
        record_session("negotiation", overall)
        st.session_state["_eval_recorded"] = True

    # Verdict banner
    verdict, msg = score_verdict(overall)
    verdict_color = "#4ade80" if overall >= 7.5 else "#fbbf24" if overall >= 5 else "#f87171"
    st.markdown(
        f"<div class='score-verdict fade-in' style='background:{verdict_color}22; color:{verdict_color}; border:1px solid {verdict_color}44; margin-bottom:1rem'>"
        f"Overall: {overall:.1f}/10 — {verdict}. {msg}</div>",
        unsafe_allow_html=True,
    )

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
        fig_polar = px.line_polar(score_df, r="Score", theta="Dimension", line_close=True, range_r=[0, 10], template="plotly_dark", title="Negotiation skill profile")
        fig_polar.update_traces(fill="toself", fillcolor="rgba(74,222,128,0.08)")
        st.plotly_chart(fig_polar, use_container_width=True)
    with chart_right:
        st.plotly_chart(px.bar(score_df, x="Score", y="Dimension", orientation="h", range_x=[0, 10], template="plotly_dark", title="Dimension scorecard", color="Score", color_continuous_scale="Teal"), use_container_width=True)

    st.divider()

    # Achievement notification
    earned = all_badges(st.session_state.session_count, st.session_state.best_score, st.session_state.modes_used)
    new_earned = [b for b in earned if b["earned"]]
    if new_earned:
        st.markdown("#### 🏆 Achievements")
        badge_cols = st.columns(min(len(new_earned), 6))
        for col, badge in zip(badge_cols, new_earned):
            col.markdown(
                f"<div class='cc-badge earned'>{badge['emoji']} {badge['name']}<div class='small-note'>{badge['desc']}</div></div>",
                unsafe_allow_html=True,
            )
        st.markdown("")

    for title, key in [("Strengths", "strengths"), ("Development areas", "weaknesses"), ("Missed opportunities", "missed_opportunities"), ("Recommended phrases", "recommended_phrases"), ("Seven-day practice plan", "seven_day_plan")]:
        with st.expander(title, expanded=title in ["Strengths", "Development areas"]):
            for item in evaluation.get(key, []):
                st.write(f"• {item}")

    report = build_report(st.session_state.scenario, evaluation, st.session_state.transcript)
    st.download_button("Download coaching report", report, file_name="careercoach_report.md", mime="text/markdown", type="primary")

    if st.button("Back to Home", use_container_width=True):
        st.session_state.page = "Home"
        st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# TIPS & RESOURCES
# ──────────────────────────────────────────────────────────────────────────────
def tips_and_resources() -> None:
    st.subheader("Tips & Resources")
    st.caption("Battle-tested strategies for negotiation and interviews.")

    tab_neg, tab_int = st.tabs(["💬 Negotiation Tips", "📋 Interview Tips"])

    with tab_neg:
        cols = st.columns(2)
        for i, tip in enumerate(NEGOTIATION_TIPS):
            with cols[i % 2]:
                st.markdown(
                    f"<div class='tip-card'>"
                    f"<div class='tip-icon'>{tip['icon']}</div>"
                    f"<div class='tip-title'>{tip['title']}</div>"
                    f"<div class='tip-body'>{tip['tip']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        st.markdown("")
        st.markdown("#### The negotiation framework")
        st.markdown("""
        <div class='panel'>
        <strong>1. Value</strong> — What you bring (skills, projects, outcomes)<br>
        <strong>2. Target</strong> — Your specific ask (with market evidence)<br>
        <strong>3. Flexibility</strong> — Total package (perks, growth, timeline)
        </div>
        """, unsafe_allow_html=True)

    with tab_int:
        cols = st.columns(2)
        for i, tip in enumerate(INTERVIEW_TIPS):
            with cols[i % 2]:
                st.markdown(
                    f"<div class='tip-card'>"
                    f"<div class='tip-icon'>{tip['icon']}</div>"
                    f"<div class='tip-title'>{tip['title']}</div>"
                    f"<div class='tip-body'>{tip['tip']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        st.markdown("")
        st.markdown("#### The STAR method")
        st.markdown("""
        <div class='panel'>
        <strong>S — Situation:</strong> Set the context briefly (20%)<br>
        <strong>T — Task:</strong> What was your specific responsibility? (10%)<br>
        <strong>A — Action:</strong> What did YOU do? Be specific. (50%)<br>
        <strong>R — Result:</strong> What was the outcome? Quantify it. (20%)
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("#### 🏆 All Achievements")
    st.caption("Earn badges by practicing. The more you practice, the more you unlock.")
    all_b = all_badges(st.session_state.session_count, st.session_state.best_score, st.session_state.modes_used)
    badge_cols = st.columns(len(all_b))
    for col, badge in zip(badge_cols, all_b):
        cls = "cc-badge earned" if badge["earned"] else "cc-badge"
        col.markdown(
            f"<div class='{cls}'>{badge['emoji']} {badge['name']}<div class='small-note'>{badge['desc']}</div></div>",
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────────────────────
# PROVIDER CONTROLS
# ──────────────────────────────────────────────────────────────────────────────
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
    default_model = secret_or_env("GROK_MODEL") or "grok-4.6"
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


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    init_state()
    engine = provider_controls()
    with st.sidebar:
        st.markdown("## 🎯 CareerCoach AI")
        st.caption("AI-powered interview & negotiation coach")
        pages = ["Home", "Practice room", "Interview workspace", "Role-fit practice", "Results dashboard", "Tips & Resources"]
        st.session_state.page = st.radio("Navigate", pages, index=pages.index(st.session_state.page) if st.session_state.page in pages else 0)
        st.divider()
        st.markdown("**Engine status**")
        st.write(f"Provider: **{engine.label}**")
        st.caption("Grok is the live provider. Demo mode is available only as a local fallback when no key is configured.")
        if getattr(engine, "last_error", ""):
            st.error(f"Grok request issue: {engine.last_error}")
        if st.button("Start a fresh session", use_container_width=True):
            reset_session()
            st.session_state["_eval_recorded"] = False
            st.rerun()

    if st.session_state.page == "Home":
        landing_page(engine)
    elif st.session_state.page == "Practice room":
        practice_room(engine)
    elif st.session_state.page == "Interview workspace":
        interview_workspace(engine)
    elif st.session_state.page == "Role-fit practice":
        role_fit_practice(engine)
    elif st.session_state.page == "Results dashboard":
        results_dashboard()
    else:
        tips_and_resources()


if __name__ == "__main__":
    main()
