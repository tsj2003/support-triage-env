# Support Triage Environment - Complete Usage Guide

## Quick Start (5 minutes)

### Prerequisites
```bash
# Python 3.10+
python --version

# Install dependencies
pip install -r server/requirements.txt
```

### 1. Run the Environment Server
```bash
# Option 1: Direct
uvicorn server.app:app --host 0.0.0.0 --port 8000

# Option 2: Python module
python -m server.app

# Option 3: Docker
docker build -t support-triage-env .
docker run -p 8000:8000 support-triage-env
```

Verify it's running:
```bash
curl http://localhost:8000/health
```

### 2. Run Inference (Baseline Agent)
```bash
# Set required environment variables
export API_BASE_URL="https://api.openai.com/v1"
export OPENAI_API_KEY="sk-..."
export MODEL_NAME="gpt-4o-mini"

# Run the inference script
python inference.py
```

You'll see output like:
```
=== billing_refund_easy ===
Goal: Resolve a duplicate billing complaint...
step=1 action=set_field reward=0.12 score=0.18 error=False
...
Final score for billing_refund_easy: 0.92

=== Summary ===
billing_refund_easy: 0.9240
shipping_vip_medium: 0.8912
security_incident_hard: 0.7654
Average: 0.8602
```

---

## Feature 1: Evaluation-as-a-Service

Generate detailed evaluation reports with recommendations.

```bash
# Same env vars as inference
export API_BASE_URL="https://api.openai.com/v1"
export OPENAI_API_KEY="sk-..."
export MODEL_NAME="gpt-4o-mini"

# Optional: Name your agent
export AGENT_NAME="My Custom Agent v1"

# Run evaluation service
python evaluation_service.py
```

**Output:**
- Console report with scores, strengths, weaknesses, recommendations
- JSON report saved to `./reports/agent_001_20240331_220000.json`

**Report includes:**
- Overall score (0-100%)
- Score by difficulty (easy/medium/hard)
- Strengths (what the agent does well)
- Weaknesses (areas to improve)
- Recommendations (actionable training suggestions)

---

## Feature 2: Agent Marketplace (Leaderboard)

Submit agents and compare rankings.

```bash
# Start interactive demo
python leaderboard.py

# Or use in your code:
from leaderboard import LeaderboardService

service = LeaderboardService()

# Submit your agent
service.submit_agent(
    agent_id="my_agent_v1",
    agent_name="My Awesome Agent",
    vendor="MyCompany",
    description="BERT-based support classifier",
    api_endpoint="https://api.mycompany.com/agent",
)

# Record evaluation results
from evaluation_service import EvaluationReport
report = ... # from evaluation_service
service.record_evaluation("my_agent_v1", report)

# View leaderboard
service.print_leaderboard(top_n=10)
```

**Database:** SQLite at `./leaderboard.db`

**Export options:**
```python
service.export_leaderboard("leaderboard.json", format="json")
service.export_leaderboard("leaderboard.csv", format="csv")
```

---

## Feature 3: Live Integration (Real CRMs)

Evaluate agents against real tickets from Zendesk/Salesforce.

### Zendesk Setup
```bash
export ZENDESK_SUBDOMAIN="yourcompany"
export ZENDESK_API_KEY="your_api_key"
export ZENDESK_EMAIL="admin@yourcompany.com"
```

```python
from live_integration import create_connector, LiveEvaluationRunner

# Create connector
config = {
    "api_key": os.getenv("ZENDESK_API_KEY"),
    "subdomain": os.getenv("ZENDESK_SUBDOMAIN"),
    "email": os.getenv("ZENDESK_EMAIL"),
}
connector = create_connector("zendesk", config)

# Run evaluation on real tickets
runner = LiveEvaluationRunner(connector)
results = runner.fetch_and_evaluate(
    agent_api_endpoint="https://your-agent-api.com/classify",
    agent_api_key="your_agent_key",
    limit=10,  # Evaluate 10 real tickets
)

# Results include quality scores for each ticket
for result in results:
    print(f"Ticket {result['ticket'].ticket_id}: "
          f"Score {result['evaluation']['quality_score']:.2%}")
```

### Salesforce Setup
```bash
export SALESFORCE_ACCESS_TOKEN="..."
export SALESFORCE_INSTANCE_URL="https://yourinstance.salesforce.com"
```

```python
config = {
    "access_token": os.getenv("SALESFORCE_ACCESS_TOKEN"),
    "instance_url": os.getenv("SALESFORCE_INSTANCE_URL"),
}
connector = create_connector("salesforce", config)
```

---

## Feature 4: Extended Domains

Additional task types: Email Triage & Code Review.

```python
from extended_domains import EMAIL_TASKS, CODE_REVIEW_TASKS

# View available tasks
print("Email tasks:", list(EMAIL_TASKS.keys()))
print("Code review tasks:", list(CODE_REVIEW_TASKS.keys()))

# Use in evaluation (integrate with environment)
from tasks import TASKS

# Add extended tasks to your environment
TASKS.update({t.task_id: t for t in EMAIL_TASKS.values()})
```

**Email Triage:** Classify emails, schedule meetings, handle escalations
**Code Review:** Find security bugs, performance issues, architecture problems

---

## Feature 5: Synthetic Data Generator

Generate unlimited training data.

```bash
# Generate demo dataset
python synthetic_data_generator.py
```

**Programmatic usage:**
```python
from synthetic_data_generator import SyntheticDataGenerator

generator = SyntheticDataGenerator(seed=42)

# Generate 1000 synthetic tickets
tickets = generator.generate_dataset(
    count=1000,
    issue_distribution={
        "billing": 0.30,
        "technical": 0.40,
        "security": 0.10,
        "feature": 0.20,
    },
    output_path="./training_data/tickets_1000.json",
)

# Generate training pairs (ticket + expected actions)
training_data = generator.generate_training_pairs(count=500)
# Use for fine-tuning your agent
```

**Output format:**
```json
{
  "ticket_id": "SYNTH_123456",
  "customer_profile": {...},
  "issue_type": "billing",
  "subject": "Unexpected charge...",
  "body": "I was charged $99.99...",
  "expected_fields": {
    "priority": "high",
    "queue": "billing",
    "issue_type": "billing_dispute"
  }
}
```

---

## Deployment to Hugging Face Spaces

### Method 1: Git Push (Recommended)
```bash
# Install HF CLI
pip install huggingface_hub

# Login
huggingface-cli login

# Create new Space (one-time)
huggingface-cli repo create support-triage-env --type space --sdk docker

# Push to Space
git init
git add .
git commit -m "Initial commit"
git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/support-triage-env
git push -u origin main
```

### Method 2: Using HuggingFace Hub
```python
from huggingface_hub import HfApi, create_repo

api = HfApi()

# Create Space
api.create_repo(
    repo_id="your-username/support-triage-env",
    repo_type="space",
    space_sdk="docker",
)

# Upload files
api.upload_folder(
    folder_path=".",
    repo_id="your-username/support-triage-env",
    repo_type="space",
)
```

### Verify Deployment
```bash
# Wait for build (2-3 minutes)
# Then test:
curl https://your-username-support-triage-env.hf.space/health
```

---

## Complete Workflow Example

```bash
# 1. Start environment
docker run -p 8000:8000 support-triage-env &

# 2. Set credentials
export API_BASE_URL="https://api.openai.com/v1"
export OPENAI_API_KEY="sk-..."
export MODEL_NAME="gpt-4o-mini"
export ENV_BASE_URL="http://localhost:8000"

# 3. Run evaluation
python evaluation_service.py

# 4. Generate synthetic training data
python -c "
from synthetic_data_generator import SyntheticDataGenerator
gen = SyntheticDataGenerator()
gen.generate_dataset(count=100, output_path='./data/synthetic_100.json')
"

# 5. Submit to leaderboard
python -c "
from leaderboard import LeaderboardService
from evaluation_service import EvaluationReport
import json

service = LeaderboardService()
service.submit_agent('my_agent', 'My Agent', 'MyCo', 'Test agent', 'http://api.example.com')

# Load report and record
with open('./reports/agent_001_*.json') as f:
    data = json.load(f)
# ... create report from data
service.print_leaderboard()
"
```

---

## Troubleshooting

### Port already in use
```bash
lsof -ti:8000 | xargs kill -9
```

### Missing dependencies
```bash
pip install -r server/requirements.txt --upgrade
```

### OpenAI API errors
- Check `API_BASE_URL` includes `/v1`
- Verify `OPENAI_API_KEY` is valid
- Try smaller `MAX_STEPS_PER_TASK` in `inference.py`

### Docker build fails
```bash
# Clean build
docker build --no-cache -t support-triage-env .
```

---

## API Endpoints (When Running)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/reset` | POST | Reset environment with task |
| `/step` | POST | Take an action |
| `/state` | GET | Get current state |

**Example API call:**
```bash
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "billing_refund_easy"}'
```

---

## Next Steps

1. **Run baseline**: `python inference.py`
2. **Evaluate**: `python evaluation_service.py`
3. **Train on synthetic data**: `python synthetic_data_generator.py`
4. **Compare on leaderboard**: `python leaderboard.py`
5. **Deploy**: Push to Hugging Face Spaces

For questions: See `README.md` or `help_openenvhackathon@scaler.com`
