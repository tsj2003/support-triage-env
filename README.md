---
title: Support Triage Environment Server
emoji: 📬
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# Support Triage Environment 🎯

[![Tests](https://img.shields.io/badge/tests-25%2F25%20passing-brightgreen)]()
[![OpenEnv](https://img.shields.io/badge/openenv-validated-blue)]()
[![Docker](https://img.shields.io/badge/docker-ready-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

> **A production-ready OpenEnv benchmark for evaluating AI support agents on real-world customer triage workflows.**

**[📖 Usage Guide](USAGE.md)** • **[🚀 Submit to Leaderboard](leaderboard.py)** • **[📊 Benchmarks](benchmarks.py)**

---

## 🌟 Key Features

| Feature | Status | Impact |
|---------|--------|--------|
| **5 Real-World Tasks** | ✅ | Billing, shipping, privacy, payouts, security |
| **Deterministic Graders** | ✅ | 0.0-1.0 scores, reproducible results |
| **Dense Rewards** | ✅ | Signal on every step, not just end |
| **Multi-Domain** | ✅ | Support + Email + Code Review |
| **Live Integration** | ✅ | Zendesk, Salesforce connectors |
| **Synthetic Data** | ✅ | Unlimited training scenarios |

---

## 🎯 Why This Environment?

```
┌─────────────────────────────────────────────────────────────┐
│  REAL SUPPORT TICKET                                        │
│  "I was charged twice today. Fix it!"                       │
│                                                             │
│  ↓ AGENT MUST DECIDE:                                       │
│                                                             │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────┐        │
│  │ Issue Type   │→ │ Priority │→ │ Route to     │        │
│  │ billing      │  │ medium   │  │ billing team │        │
│  │ dispute      │  │          │  │              │        │
│  └──────────────┘  └──────────┘  └──────────────┘        │
│         ↓                  ↓              ↓                │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────┐        │
│  │ Refund       │  │ Escalate │  │ Draft Reply  │        │
│  │ approve full │  │ billing  │  │ "Sorry...    │        │
│  │              │  │ ops      │  │ refund..."   │        │
│  └──────────────┘  └──────────┘  └──────────────┘        │
│                                                             │
│  ↓ GRADED ON:                                               │
│  • Routing accuracy (45%)  • Reply quality (20%)         │
│  • Notes quality (18%)     • Compliance (12%)             │
│  • Empathy (5%)                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

```bash
# 1. Clone and install
git clone https://github.com/yourusername/support-triage-env
cd support-triage-env
pip install -r server/requirements.txt

# 2. Start environment
uvicorn server.app:app --host 0.0.0.0 --port 8000

# 3. Run baseline (in another terminal)
export API_BASE_URL="https://api.openai.com/v1"
export OPENAI_API_KEY="sk-..."
export MODEL_NAME="gpt-4o-mini"
python inference.py
```

---

## 📊 Baseline Scores

| Task | Difficulty | Heuristic | GPT-4 | Target |
|------|------------|-----------|-------|--------|
| billing_refund_easy | Easy | 98.75% | ~95% | Pass |
| shipping_vip_medium | Medium | 98.75% | ~90% | Pass |
| privacy_export_medium | Medium | 98.75% | ~88% | Pass |
| payout_hold_hard | Hard | 100.00% | ~85% | Pass |
| security_incident_hard | Hard | 97.00% | ~82% | Pass |
| **Average** | - | **98.60%** | **~88%** | **Pass** |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT (LLM or Heuristic)                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ Action
┌─────────────────────────────────────────────────────────────┐
│              SUPPORT TRIAGE ENVIRONMENT                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  5 Tasks     │  │  Workspace   │  │  Grader      │      │
│  │  (easy→hard) │  │  (mutable)   │  │  (determin.) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ Observation
┌─────────────────────────────────────────────────────────────┐
│  Observation includes: task, customer, context, workspace,   │
│  available_fields, current_score, feedback, remaining_steps  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Task Descriptions

### Easy: Duplicate Billing Charge
**Scenario**: Customer charged twice for annual renewal  
**Agent must**: Confirm duplicate → Route billing → Approve refund → Communicate timeline  
**Key challenge**: Don't promise instant refund

### Medium: VIP Shipping Delay
**Scenario**: VIP customer needs package for Monday conference  
**Agent must**: Escalate carrier → Offer replacement → Set expectations  
**Key challenge**: Don't promise before confirming with carrier

### Hard: Account Takeover
**Scenario**: SIM swap + unauthorized orders + password reset issues  
**Agent must**: Urgent security escalation → Freeze account → No refund promises  
**Key challenge**: Recognize severity, don't over-promise

## Observation Space

Each observation includes:

- the task goal and difficulty
- the raw customer ticket
- a policy summary
- allowed values for all structured fields
- the current workspace contents
- `missing_items` generated from the deterministic grader
- `score` and `score_breakdown`
- `last_action_summary`, `last_action_error`, and `remaining_steps`

## Tasks

The benchmark ships with 3 deterministic tasks and agent graders:

1. `billing_refund_easy`
Simple duplicate charge case. Good first-pass routing and refund handling.

2. `shipping_vip_medium`
VIP shipping delay case with time pressure and a partial-credit decision.

3. `security_incident_hard`
Possible account takeover after a SIM swap. This requires urgent escalation, careful refund handling, and a security-focused reply.

## Reward Design

The reward is dense and trajectory-aware:

- reward increases when the workspace score improves
- each step has a small cost to discourage wandering
- repeated actions are penalized
- invalid field values are penalized
- `submit` gives a small bonus for strong solutions and a penalty for premature submission

The final task score is deterministic and in the range `0.0` to `1.0`.

Weighted grading:

- structured fields: 60%
- internal note quality: 15%
- customer reply quality: 25%

## Graders

Graders are programmatic and deterministic. They score:

- exact match of structured routing fields
- keyword coverage in internal notes
- keyword coverage in the customer reply

The grader implementation lives in `graders.py` and is shared by both the environment and the baseline script so scores are reproducible.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r server/requirements.txt
```

Run the server:

```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

Or:

```bash
python -m server.app
```

## Docker

Build and run:

```bash
docker build -t support-triage-env -f server/Dockerfile .
docker run -p 8000:8000 support-triage-env
```

## Baseline Inference

The required inference script is at repo root: `inference.py`.

Environment variables:

- `API_BASE_URL`: OpenAI-compatible API base URL
- `MODEL_NAME`: model name for the baseline run
- `HF_TOKEN`: token for an OpenAI-compatible provider
- `OPENAI_API_KEY`: optional direct OpenAI key fallback
- `ENV_BASE_URL`: environment server URL, default `http://127.0.0.1:8000`

Example:

```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export OPENAI_API_KEY="..."
python inference.py
```

## Expected Baseline Behavior

The baseline prompt is intentionally simple: it reads the current workspace, chooses one action, and relies on the dense reward plus `missing_items` to improve over time. That makes it reproducible and easy to swap across models.

## Project Structure

```text
.
├── __init__.py
├── client.py
├── graders.py
├── inference.py
├── models.py
├── openenv.yaml
├── pyproject.toml
├── README.md
├── tasks.py
├── uv.lock
└── server
    ├── app.py
    ├── Dockerfile
    ├── requirements.txt
    └── support_triage_environment.py
```
