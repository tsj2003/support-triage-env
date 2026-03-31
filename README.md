# 📬 Support Triage Environment

Hey there! This is my OpenEnv hackathon submission - a real-world benchmark for training AI agents to handle customer support tickets. Not a game, not a toy - actual support workflows that real teams deal with every day.

Built this because I noticed most AI benchmarks focus on games or synthetic tasks, but support teams need agents that can actually route tickets, follow policy, and write helpful replies. So here we are!

## ✨ What's This About?

Imagine you're a support agent and this ticket comes in:

> *"I was charged twice for my annual subscription today. Fix it now and tell me when I'll get my money back!"*

Your AI agent needs to:
1. 🏷️ Figure out it's a **billing dispute** (not a technical issue)
2. 🚨 Set priority to **medium** (urgent but not site-down)
3. 📁 Route to the **billing** queue
4. 💰 Choose **approve full refund** (not investigate first)
5. 📝 Add internal notes with evidence
6. ✉️ Draft an empathetic reply
7. ✅ Submit the case

Sounds simple? Wait till you see the hard tasks involving account takeovers and payout holds 😅

## 🎮 The 5 Tasks

| Task | Difficulty | What Makes It Tricky |
|------|------------|---------------------|
| **billing_refund_easy** 🟢 | Easy | Classic duplicate charge - good starter |
| **shipping_vip_medium** 🟡 | Medium | VIP customer + time pressure + conference deadline |
| **privacy_export_medium** 🟡 | Medium | GDPR request, closed account, identity verification |
| **payout_hold_hard** 🔴 | Hard | Creator payout frozen + velocity spike + can't promise immediate release |
| **security_incident_hard** 🔴 | Hard | SIM swap attack + unauthorized orders + urgent escalation |

The hard tasks will mess with your agent if it's not careful about policy compliance!

## 🚀 Quick Start (5 min)

```bash
# Install deps
pip install -r server/requirements.txt

# Fire up the server
uvicorn server.app:app --host 0.0.0.0 --port 8000

# In another terminal, run the baseline
export API_BASE_URL="https://api.openai.com/v1"
export OPENAI_API_KEY="sk-your-key-here"
export MODEL_NAME="gpt-4o-mini"
python inference.py
```

That's it! You'll see scores for all 5 tasks.

## 🏗️ How It Works

**Agent takes actions:**
- `set_field` - Update ticket fields (issue_type, priority, queue, etc.)
- `add_note` - Add internal notes for the team
- `draft_reply` - Write response to customer
- `submit` - Done! Case goes to grading

**Environment responds with:**
- Current workspace state
- Score (0.0 to 1.0)
- What you got right/wrong
- How many steps left

**Grading is deterministic** - same actions = same score, always. No randomness, no "vibes-based" scoring.

## 📊 Baseline Scores

Here's what my heuristic policy gets (no LLM calls, just hardcoded rules):

| Task | Score | Notes |
|------|-------|-------|
| billing_refund_easy | 98.75% | Routing + refund logic |
| shipping_vip_medium | 98.75% | VIP handling + carrier escalation |
| privacy_export_medium | 98.75% | Compliance + timeline management |
| payout_hold_hard | 100.00% | No immediate promises |
| security_incident_hard | 97.00% | Urgent escalation + freeze account |
| **Average** | **98.60%** | Pretty solid baseline! |

LLM-based agents (GPT-4, Claude) typically score 82-95% on the hard tasks - there's room for improvement!

## 🎯 Grading Breakdown

Scores aren't just pass/fail. We check:

- **Routing & Resolution (45%)** - Did you send it to the right team?
- **Customer Reply (20%)** - Clear, empathetic, actionable?
- **Internal Notes (18%)** - Good evidence and reasoning?
- **Policy Compliance (12%)** - No over-promising?
- **Tone & Clarity (5%)** - Human-sounding?

## 🐳 Docker

```bash
docker build -t support-triage-env .
docker run -p 8000:8000 support-triage-env
```

Health check: `curl http://localhost:8000/health`

## 📁 Project Structure

```
.
├── inference.py          # Run agents against the benchmark
├── models.py             # Pydantic types
├── tasks.py              # Task definitions
├── graders.py            # Scoring logic
├── server/               # FastAPI environment server
│   ├── app.py
│   ├── support_triage_environment.py
│   └── Dockerfile
└── tests/                # 25 tests, all passing ✓
```

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
# 25 tests should pass
```

## 🔥 Beyond The Basics

Threw in some extra stuff for the "startup features" angle:

- **evaluation_service.py** - Run batch evals, generate reports
- **leaderboard.py** - Compare agents, rank submissions
- **live_integration.py** - Connect to real Zendesk/Salesforce
- **extended_domains.py** - Email triage + code review tasks
- **synthetic_data_generator.py** - Unlimited training data

Check `USAGE.md` for details on these.

## 🌐 Live Demo

Try it on Hugging Face Spaces:  
**https://huggingface.co/spaces/Tarandeep1111/support-triage-env**

API endpoint: `https://tarandeep1111-support-triage-env.hf.space`

## 📝 Why I Built This

Working on support tools, I kept hitting the same problem: how do you know if your AI agent is actually good at support? Existing benchmarks test chat quality in isolation, but real support needs:

- Structured decision making (routing, priority)
- Policy awareness (can't refund without investigation)
- Empathy + clarity in writing
- Documentation for the team

This environment tests all of that together. Dense rewards so agents learn from every step, not just at the end. Deterministic grading so you can actually compare approaches.

Hope it's useful for training the next gen of support agents! 🚀

---

**Built for OpenEnv Hackathon Round 1** | **Solo submission by Tarandeep Singh Juneja**

📧 tarandeepjuneja11@gmail.com
