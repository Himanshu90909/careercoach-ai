from __future__ import annotations

import os
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from modules.ai_engine import AIEngine
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
        "page": "Practice room",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_session() -> None:
    for key in ["scenario", "transcript", "round_scores", "last_ai_response", "evaluation"]:
        st.session_state[key] = None if key in ["scenario", "evaluation"] else ([] if key in ["transcript", "round_scores"] else "")


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


def main() -> None:
    init_state()
    engine = AIEngine()
    with st.sidebar:
        st.markdown("## `careercoach_ai`")
        st.caption("Voice-driven negotiation practice")
        st.session_state.page = st.radio("Navigate", ["Practice room", "Results dashboard"], index=0 if st.session_state.page == "Practice room" else 1)
        st.divider()
        st.markdown("**Engine status**")
        st.success("Gemini connected") if engine.available else st.warning("Demo mode — add GEMINI_API_KEY for live AI")
        st.caption("Demo mode remains fully usable with deterministic HR prompts and scoring.")
    st.markdown('<div class="hero"><div class="kicker">// internship readiness lab</div><h1>CareerCoach AI</h1><p>Practise the conversation before the conversation. Negotiate with a demanding virtual HR manager, then turn your performance into a measurable coaching plan.</p></div>', unsafe_allow_html=True)
    st.write("")
    if st.session_state.page == "Practice room":
        practice_room(engine)
    else:
        results_dashboard()


if __name__ == "__main__":
    main()
