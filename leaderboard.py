"""Agent Marketplace: Leaderboard and ranking system for support agents."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional

from evaluation_service import EvaluationReport, TaskResult


@dataclass
class AgentSubmission:
    """Agent submitted for evaluation."""
    agent_id: str
    agent_name: str
    vendor: str
    description: str
    api_endpoint: str  # Where to call the agent
    api_key: Optional[str]
    submitted_at: str
    status: str = "pending"  # pending, running, completed, failed


@dataclass
class LeaderboardEntry:
    """Entry in the leaderboard."""
    rank: int
    agent_id: str
    agent_name: str
    vendor: str
    overall_score: float
    easy_score: float
    medium_score: float
    hard_score: float
    total_evaluations: int
    last_evaluated: str
    is_official: bool = False  # Official vendor submission vs community


class LeaderboardDatabase:
    """SQLite database for storing leaderboard data."""
    
    def __init__(self, db_path: str = "./leaderboard.db") -> None:
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    vendor TEXT NOT NULL,
                    description TEXT,
                    api_endpoint TEXT,
                    api_key TEXT,
                    submitted_at TEXT,
                    status TEXT DEFAULT 'pending'
                );
                
                CREATE TABLE IF NOT EXISTS evaluations (
                    evaluation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    evaluation_date TEXT NOT NULL,
                    overall_score REAL NOT NULL,
                    easy_score REAL,
                    medium_score REAL,
                    hard_score REAL,
                    report_path TEXT,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                );
                
                CREATE TABLE IF NOT EXISTS task_scores (
                    evaluation_id INTEGER,
                    task_id TEXT NOT NULL,
                    difficulty TEXT,
                    score REAL NOT NULL,
                    FOREIGN KEY (evaluation_id) REFERENCES evaluations(evaluation_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_evaluations_agent 
                    ON evaluations(agent_id);
                CREATE INDEX IF NOT EXISTS idx_evaluations_score 
                    ON evaluations(overall_score DESC);
            """)
    
    def submit_agent(self, submission: AgentSubmission) -> str:
        """Submit a new agent for evaluation."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO agents 
                (agent_id, agent_name, vendor, description, api_endpoint, api_key, submitted_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    submission.agent_id,
                    submission.agent_name,
                    submission.vendor,
                    submission.description,
                    submission.api_endpoint,
                    submission.api_key,
                    submission.submitted_at,
                    submission.status,
                ),
            )
        return submission.agent_id
    
    def save_evaluation(self, agent_id: str, report: EvaluationReport) -> int:
        """Save an evaluation result."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO evaluations (agent_id, evaluation_date, overall_score, easy_score, medium_score, hard_score)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    agent_id,
                    report.evaluation_date,
                    report.overall_score,
                    report.score_by_difficulty.get("easy"),
                    report.score_by_difficulty.get("medium"),
                    report.score_by_difficulty.get("hard"),
                ),
            )
            evaluation_id = cursor.lastrowid
            
            # Save individual task scores
            for task_result in report.task_results:
                conn.execute(
                    """
                    INSERT INTO task_scores (evaluation_id, task_id, difficulty, score)
                    VALUES (?, ?, ?, ?)
                    """,
                    (evaluation_id, task_result.task_id, task_result.difficulty, task_result.final_score),
                )
            
            # Update agent status
            conn.execute(
                "UPDATE agents SET status = 'completed' WHERE agent_id = ?",
                (agent_id,),
            )
            
        return evaluation_id
    
    def get_leaderboard(
        self,
        difficulty: Optional[str] = None,
        vendor: Optional[str] = None,
        official_only: bool = False,
    ) -> List[LeaderboardEntry]:
        """Get current leaderboard."""
        query = """
            SELECT 
                a.agent_id,
                a.agent_name,
                a.vendor,
                e.overall_score,
                e.easy_score,
                e.medium_score,
                e.hard_score,
                COUNT(e2.evaluation_id) as total_evaluations,
                MAX(e.evaluation_date) as last_evaluated
            FROM agents a
            JOIN evaluations e ON a.agent_id = e.agent_id
            JOIN evaluations e2 ON a.agent_id = e2.agent_id
            WHERE e.evaluation_id = (
                SELECT MAX(evaluation_id) 
                FROM evaluations 
                WHERE agent_id = a.agent_id
            )
        """
        params = []
        
        if vendor:
            query += " AND a.vendor = ?"
            params.append(vendor)
        
        query += """
            GROUP BY a.agent_id
            ORDER BY e.overall_score DESC
        """
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
        
        entries = []
        for rank, row in enumerate(rows, 1):
            score = row["overall_score"]
            if difficulty:
                score = row[f"{difficulty}_score"] or 0.0
            
            entries.append(LeaderboardEntry(
                rank=rank,
                agent_id=row["agent_id"],
                agent_name=row["agent_name"],
                vendor=row["vendor"],
                overall_score=score,
                easy_score=row["easy_score"] or 0.0,
                medium_score=row["medium_score"] or 0.0,
                hard_score=row["hard_score"] or 0.0,
                total_evaluations=row["total_evaluations"],
                last_evaluated=row["last_evaluated"],
            ))
        
        return entries
    
    def get_agent_history(self, agent_id: str) -> List[Dict]:
        """Get evaluation history for an agent."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT evaluation_date, overall_score, easy_score, medium_score, hard_score
                FROM evaluations
                WHERE agent_id = ?
                ORDER BY evaluation_date ASC
                """,
                (agent_id,),
            ).fetchall()
        
        return [dict(row) for row in rows]
    
    def compare_agents(self, agent_ids: List[str]) -> Dict:
        """Compare multiple agents side by side."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            placeholders = ",".join("?" * len(agent_ids))
            rows = conn.execute(
                f"""
                SELECT 
                    a.agent_id,
                    a.agent_name,
                    a.vendor,
                    e.overall_score,
                    e.easy_score,
                    e.medium_score,
                    e.hard_score
                FROM agents a
                JOIN evaluations e ON a.agent_id = e.agent_id
                WHERE a.agent_id IN ({placeholders})
                AND e.evaluation_id = (
                    SELECT MAX(evaluation_id) 
                    FROM evaluations 
                    WHERE agent_id = a.agent_id
                )
                """,
                agent_ids,
            ).fetchall()
        
        return {
            "agents": [dict(row) for row in rows],
            "best_overall": max(rows, key=lambda r: r["overall_score"])["agent_name"],
            "best_easy": max(rows, key=lambda r: r["easy_score"] or 0)["agent_name"],
            "best_hard": max(rows, key=lambda r: r["hard_score"] or 0)["agent_name"],
        }


class LeaderboardService:
    """Service for managing the leaderboard."""
    
    def __init__(self, db: Optional[LeaderboardDatabase] = None) -> None:
        self.db = db or LeaderboardDatabase()
    
    def submit_agent(
        self,
        agent_id: str,
        agent_name: str,
        vendor: str,
        description: str,
        api_endpoint: str,
        api_key: Optional[str] = None,
    ) -> str:
        """Submit an agent for leaderboard evaluation."""
        submission = AgentSubmission(
            agent_id=agent_id,
            agent_name=agent_name,
            vendor=vendor,
            description=description,
            api_endpoint=api_endpoint,
            api_key=api_key,
            submitted_at=datetime.now().isoformat(),
        )
        return self.db.submit_agent(submission)
    
    def record_evaluation(self, agent_id: str, report: EvaluationReport) -> int:
        """Record an evaluation result."""
        return self.db.save_evaluation(agent_id, report)
    
    def get_leaderboard(
        self,
        difficulty: Optional[str] = None,
        vendor: Optional[str] = None,
    ) -> List[LeaderboardEntry]:
        """Get the current leaderboard."""
        return self.db.get_leaderboard(difficulty=difficulty, vendor=vendor)
    
    def print_leaderboard(
        self,
        difficulty: Optional[str] = None,
        top_n: int = 10,
    ) -> None:
        """Print a formatted leaderboard."""
        entries = self.get_leaderboard(difficulty=difficulty)
        
        print("\n" + "=" * 100)
        title = f"🏆 SUPPORT AGENT LEADERBOARD"
        if difficulty:
            title += f" - {difficulty.upper()} TASKS"
        print(f"{title:^100}")
        print("=" * 100)
        
        print(f"\n{'Rank':<6} {'Agent':<25} {'Vendor':<20} {'Overall':<10} {'Easy':<8} {'Medium':<8} {'Hard':<8}")
        print("-" * 100)
        
        for entry in entries[:top_n]:
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(entry.rank, "  ")
            print(
                f"{medal} {entry.rank:<4} "
                f"{entry.agent_name[:24]:<25} "
                f"{entry.vendor[:19]:<20} "
                f"{entry.overall_score:>6.1%}  "
                f"{entry.easy_score:>6.1%}  "
                f"{entry.medium_score:>6.1%}  "
                f"{entry.hard_score:>6.1%}"
            )
        
        print("=" * 100)
        print(f"\nTotal agents evaluated: {len(entries)}")
    
    def export_leaderboard(self, filepath: str, format: str = "json") -> None:
        """Export leaderboard to file."""
        entries = self.get_leaderboard()
        
        if format == "json":
            data = {
                "generated_at": datetime.now().isoformat(),
                "total_agents": len(entries),
                "leaderboard": [asdict(e) for e in entries],
            }
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
        elif format == "csv":
            import csv
            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "rank", "agent_id", "agent_name", "vendor", "overall_score",
                    "easy_score", "medium_score", "hard_score", "total_evaluations"
                ])
                for e in entries:
                    writer.writerow([
                        e.rank, e.agent_id, e.agent_name, e.vendor,
                        e.overall_score, e.easy_score, e.medium_score,
                        e.hard_score, e.total_evaluations,
                    ])


def main() -> None:
    """Demo the leaderboard functionality."""
    service = LeaderboardService()
    
    # Example: Submit some agents
    service.submit_agent(
        agent_id="zendesk_ai",
        agent_name="Zendesk AI",
        vendor="Zendesk",
        description="Official Zendesk AI agent",
        api_endpoint="https://api.zendesk.com/v2/ai",
    )
    
    service.submit_agent(
        agent_id="intercom_fin",
        agent_name="Fin",
        vendor="Intercom",
        description="Intercom's AI support agent",
        api_endpoint="https://api.intercom.io/fin",
    )
    
    service.submit_agent(
        agent_id="gorgias_automation",
        agent_name="Gorgias Automation",
        vendor="Gorgias",
        description="E-commerce support AI",
        api_endpoint="https://api.gorgias.com/automation",
    )
    
    print("Agents submitted successfully!")
    print("\nTo run evaluations and populate the leaderboard:")
    print("  python evaluation_service.py")
    print("  # Then record results with service.record_evaluation()")


if __name__ == "__main__":
    main()
