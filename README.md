# CareerCoach AI

Your AI-powered interview & negotiation coach. Practice salary negotiations with a realistic HR simulation, prepare for role-specific interviews, and analyze your resume-to-role fit — all grounded in real job descriptions.

## Features

- **Negotiation Practice** — Simulate a salary negotiation with an AI HR manager and get a detailed scorecard across 6 dimensions.
- **Interview Prep** — Paste any job description and get role-specific questions, coaching feedback, and skill ranking.
- **Role-Fit Analysis** — Upload your resume and job description to see match scores, skill gaps, and personalized practice questions.
- **Quick-Start Templates** — Jump into a pre-built scenario with one click. No setup required.
- **Achievement System** — Earn badges as you practice. Track your progress across sessions.
- **Tips & Resources** — Battle-tested strategies for negotiation and interviews.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app works in **Demo mode** without any API key. For full AI-powered responses, add a Grok API key in the sidebar.

## Quick-Start Templates

| Template | Industry | Offer → Target |
|----------|----------|---------------|
| Software Engineering Intern | Technology | ₹25k → ₹40k |
| Data Analyst Intern | FinTech | ₹30k → ₹50k |
| Product Manager Intern | EdTech | ₹35k → ₹55k |
| Consulting Intern | Consulting | ₹40k → ₹65k |

## Configuration

### AI Provider

- **Grok** (xAI) — Set `GROK_API_KEY` in environment, Streamlit Secrets, or the sidebar input.
- **Demo mode** — No API key needed. Uses deterministic local fallbacks.

### Environment Variables

```bash
GROK_API_KEY=your_api_key_here
GROK_MODEL=grok-4.6  # optional
```

## Architecture

```
app.py                     # Main Streamlit app
modules/
  ai_engine.py            # AI provider abstraction (Grok + demo fallback)
  document_parser.py      # Resume/JD file parsing (PDF, DOCX, TXT)
  prompts.py              # LLM prompt construction
  scoring.py              # Deterministic scoring helpers
  report_generator.py     # Markdown report generation
  progress.py             # Quick-start templates, tips, achievements
tests/                    # Test suite
docs/                     # Architecture & rubric docs
```

## Tech Stack

- **Streamlit** — Web framework
- **Plotly** — Visualizations
- **Grok (xAI)** — AI provider with demo fallback
- **pypdf / python-docx** — Document parsing

## License

This project is for educational and personal use.
