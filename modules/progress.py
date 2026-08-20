"""Quick-start templates, coaching tips, achievements, and score verdicts."""

from __future__ import annotations

QUICK_START_TEMPLATES = [
    {
        "title": "Software Engineering Intern",
        "subtitle": "Tech · Hybrid · ₹25k → ₹40k",
        "tag": "Popular",
        "tag_color": "#4ade80",
        "scenario": {
            "role": "Software Engineering Intern",
            "industry": "Technology",
            "experience": "Student / first internship",
            "work_mode": "Hybrid",
            "current_offer": 25000.0,
            "target_amount": 40000.0,
            "minimum_amount": 32000.0,
            "style": "Evidence-led",
        },
    },
    {
        "title": "Data Analyst Intern",
        "subtitle": "FinTech · Remote · ₹30k → ₹50k",
        "tag": "Remote",
        "tag_color": "#60a5fa",
        "scenario": {
            "role": "Data Analyst Intern",
            "industry": "FinTech",
            "experience": "Final-year student",
            "work_mode": "Remote",
            "current_offer": 30000.0,
            "target_amount": 50000.0,
            "minimum_amount": 38000.0,
            "style": "Collaborative",
        },
    },
    {
        "title": "Product Manager Intern",
        "subtitle": "EdTech · On-site · ₹35k → ₹55k",
        "tag": "Trending",
        "tag_color": "#fbbf24",
        "scenario": {
            "role": "Product Manager Intern",
            "industry": "EdTech",
            "experience": "Recent graduate",
            "work_mode": "On-site",
            "current_offer": 35000.0,
            "target_amount": 55000.0,
            "minimum_amount": 42000.0,
            "style": "Direct and concise",
        },
    },
    {
        "title": "Consulting Intern",
        "subtitle": "Consulting · Hybrid · ₹40k → ₹65k",
        "tag": "Challenging",
        "tag_color": "#a78bfa",
        "scenario": {
            "role": "Consulting Intern",
            "industry": "Consulting",
            "experience": "Final-year student",
            "work_mode": "Hybrid",
            "current_offer": 40000.0,
            "target_amount": 65000.0,
            "minimum_amount": 48000.0,
            "style": "Evidence-led",
        },
    },
]

NEGOTIATION_TIPS = [
    {"title": "Lead with value, not need", "tip": "Open with what you bring — specific skills, projects, measurable results. Never start with 'I need more money.'", "icon": "🎯"},
    {"title": "Know your market range", "tip": "Research salary ranges before negotiating. Glassdoor, Levels.fyi, and LinkedIn Salary are great starting points.", "icon": "📊"},
    {"title": "Anchor higher, stay flexible", "tip": "Ask for 10-20% above your target. This gives room to negotiate down while still landing above your minimum.", "icon": "⚓"},
    {"title": "Total package matters", "tip": "If base salary is fixed, negotiate learning budget, remote days, conference travel, or a signing bonus.", "icon": "📦"},
    {"title": "Use silence strategically", "tip": "After stating your number, stop talking. Let the HR manager respond first. Silence shows confidence.", "icon": "🤫"},
    {"title": "Quantify everything", "tip": "'Improved performance' is weak. 'Reduced API latency by 40% for 200k users' is strong. Numbers win.", "icon": "🔢"},
]

INTERVIEW_TIPS = [
    {"title": "Master the STAR method", "tip": "Situation -> Task -> Action -> Result. Spend 20% on context, 60% on YOUR action, 20% on results.", "icon": "⭐"},
    {"title": "Ask clarifying questions", "tip": "For technical questions, restate the problem and ask about constraints. Shows methodical thinking.", "icon": "❓"},
    {"title": "Talk through your thinking", "tip": "In coding or case questions, narrate your approach. Interviewers care about your process, not just the answer.", "icon": "💭"},
    {"title": "Always have questions ready", "tip": "Prepare 3-5 questions about the role, team, or culture. Shows genuine interest and engagement.", "icon": "💬"},
    {"title": "Connect answers to the role", "tip": "Tie every answer back to internship requirements. Use 'This is relevant because in this role...'", "icon": "🔗"},
    {"title": "Nail 'Tell me about yourself'", "tip": "Present -> Past -> Future: who you are now, what you've done, why this role is next. 90 seconds max.", "icon": "🎤"},
]

ACHIEVEMENT_BADGES = [
    {"name": "First Steps", "emoji": "🎯", "desc": "Complete your first practice session", "threshold": 1, "metric": "sessions"},
    {"name": "Getting Serious", "emoji": "💪", "desc": "Complete 3 practice sessions", "threshold": 3, "metric": "sessions"},
    {"name": "Dedicated", "emoji": "🔥", "desc": "Complete 5 practice sessions", "threshold": 5, "metric": "sessions"},
    {"name": "Interview Pro", "emoji": "⚡", "desc": "Complete 10 practice sessions", "threshold": 10, "metric": "sessions"},
    {"name": "Sharp Negotiator", "emoji": "🏆", "desc": "Score 8+ on a negotiation session", "threshold": 8.0, "metric": "score"},
    {"name": "Well-Rounded", "emoji": "🌟", "desc": "Try all three practice modes", "threshold": 3, "metric": "modes"},
]

SCORE_VERDICTS = [
    (9.0, "Outstanding", "You're in the top tier. Walk into that negotiation with confidence."),
    (7.5, "Strong", "Solid performance. A few tweaks and you'll be unstoppable."),
    (6.0, "Good progress", "You're on the right track. Focus on the development areas below."),
    (4.0, "Needs work", "Keep practicing - the frameworks above will help you level up fast."),
    (0.0, "Keep going", "Every expert started here. Use the tips and try again."),
]


def score_verdict(score: float) -> tuple[str, str]:
    """Return (verdict_label, encouragement_message) for a given score 0-10."""
    for threshold, verdict, message in SCORE_VERDICTS:
        if score >= threshold:
            return verdict, message
    return SCORE_VERDICTS[-1][1], SCORE_VERDICTS[-1][2]


def get_earned_badges(session_count: int, best_score: float, modes_used: set) -> list[dict]:
    """Return list of earned badge dicts based on session count, best score, and modes used."""
    earned = []
    for badge in ACHIEVEMENT_BADGES:
        metric = badge.get("metric", "sessions")
        if metric == "sessions" and session_count >= badge["threshold"]:
            earned.append(badge)
        elif metric == "score" and best_score >= badge["threshold"]:
            earned.append(badge)
        elif metric == "modes" and len(modes_used) >= badge["threshold"]:
            earned.append(badge)
    return earned


def all_badges(session_count: int, best_score: float, modes_used: set) -> list[dict]:
    """Return all badges with an 'earned' flag."""
    earned_ids = {b["name"] for b in get_earned_badges(session_count, best_score, modes_used)}
    result = []
    for badge in ACHIEVEMENT_BADGES:
        b = dict(badge)
        b["earned"] = badge["name"] in earned_ids
        result.append(b)
    return result
