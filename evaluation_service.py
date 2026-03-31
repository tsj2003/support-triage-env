"""Evaluation-as-a-Service: Run agent evaluations and generate reports."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openenv.core import GenericAction, GenericEnvClient

from inference import get_openai_client, parse_model_action, request_model_action, validate_environment


@dataclass
class TaskResult:
    """Result of a single task evaluation."""
    task_id: str
    difficulty: str
    final_score: float
    steps_taken: int
    actions: List[Dict[str, Any]]
    rewards: List[float]
    scores: List[float]
    errors: int
    duration_seconds: float
    trace: List[str] = field(default_factory=list)


@dataclass
class EvaluationReport:
    """Complete evaluation report for an agent."""
    agent_id: str
    agent_name: str
    evaluation_date: str
    total_tasks: int
    overall_score: float
    task_results: List[TaskResult]
    score_by_difficulty: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    raw_data: Dict[str, Any] = field(default_factory=dict)


def run_single_task(
    client: OpenAI,
    task_id: str,
    max_steps: int = 14,
    env_base_url: str = "http://127.0.0.1:8000",
) -> TaskResult:
    """Run a single task evaluation."""
    start_time = time.time()
    history: List[str] = []
    actions: List[Dict[str, Any]] = []
    rewards: List[float] = []
    scores: List[float] = []
    errors = 0
    trace: List[str] = []

    with GenericEnvClient(base_url=env_base_url).sync() as env:
        result = env.reset(task_id=task_id)
        observation = result.observation

        for step in range(1, max_steps + 1):
            if result.done:
                break

            action = request_model_action(client, observation, history, step)
            actions.append(action)
            
            result = env.step(GenericAction(**action))
            observation = result.observation

            rewards.append(result.reward or 0.0)
            scores.append(observation.get("score", 0.0))
            
            if observation.get("last_action_error"):
                errors += 1

            history_line = (
                f"step={step} action={action.get('kind')} "
                f"reward={result.reward:.3f} score={observation.get('score'):.3f}"
            )
            history.append(history_line)
            trace.append(history_line)

            if result.done:
                break

    duration = time.time() - start_time

    return TaskResult(
        task_id=task_id,
        difficulty=observation.get("difficulty", "unknown"),
        final_score=observation.get("score", 0.0),
        steps_taken=len(actions),
        actions=actions,
        rewards=rewards,
        scores=scores,
        errors=errors,
        duration_seconds=duration,
        trace=trace,
    )


def generate_report(
    agent_id: str,
    agent_name: str,
    task_results: List[TaskResult],
) -> EvaluationReport:
    """Generate comprehensive evaluation report."""
    
    # Calculate overall score
    scores = [r.final_score for r in task_results]
    overall_score = mean(scores) if scores else 0.0

    # Score by difficulty
    difficulty_groups: Dict[str, List[float]] = {}
    for result in task_results:
        difficulty_groups.setdefault(result.difficulty, []).append(result.final_score)
    
    score_by_difficulty = {
        diff: mean(scores) for diff, scores in difficulty_groups.items()
    }

    # Identify strengths and weaknesses
    strengths = []
    weaknesses = []
    
    # Best performing task
    best_task = max(task_results, key=lambda r: r.final_score)
    if best_task.final_score > 0.8:
        strengths.append(f"Excellent performance on {best_task.task_id} (score: {best_task.final_score:.2f})")
    
    # Worst performing task
    worst_task = min(task_results, key=lambda r: r.final_score)
    if worst_task.final_score < 0.5:
        weaknesses.append(f"Struggles with {worst_task.task_id} (score: {worst_task.final_score:.2f})")
    
    # Error rate analysis
    total_errors = sum(r.errors for r in task_results)
    total_steps = sum(r.steps_taken for r in task_results)
    error_rate = total_errors / total_steps if total_steps > 0 else 0
    
    if error_rate > 0.2:
        weaknesses.append(f"High error rate: {error_rate:.1%} of actions were invalid")
    else:
        strengths.append(f"Low error rate: {error_rate:.1%} - good action compliance")

    # Difficulty progression
    if "easy" in score_by_difficulty and "hard" in score_by_difficulty:
        easy_score = score_by_difficulty["easy"]
        hard_score = score_by_difficulty["hard"]
        if hard_score < easy_score * 0.7:
            weaknesses.append(f"Significant performance drop on hard tasks ({easy_score:.2f} → {hard_score:.2f})")

    # Generate recommendations
    recommendations = []
    
    if worst_task.final_score < 0.5:
        recommendations.append(f"Focus training on {worst_task.task_id} - lowest performing area")
    
    if error_rate > 0.15:
        recommendations.append("Improve action validation - too many invalid actions submitted")
    
    if any(r.steps_taken >= 14 for r in task_results):
        recommendations.append("Optimize decision speed - some tasks hit step limit")

    if not recommendations:
        recommendations.append("Agent is performing well across all tasks - consider expanding to new domains")

    return EvaluationReport(
        agent_id=agent_id,
        agent_name=agent_name,
        evaluation_date=datetime.now().isoformat(),
        total_tasks=len(task_results),
        overall_score=overall_score,
        task_results=task_results,
        score_by_difficulty=score_by_difficulty,
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations,
        raw_data={
            "total_errors": total_errors,
            "total_steps": total_steps,
            "error_rate": error_rate,
            "score_std": stdev(scores) if len(scores) > 1 else 0.0,
        },
    )


def save_report(report: EvaluationReport, output_dir: str = "./reports") -> str:
    """Save report to file and return path."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{report.agent_id}_{timestamp}.json"
    filepath = output_path / filename

    # Convert dataclass to dict
    report_dict = {
        "agent_id": report.agent_id,
        "agent_name": report.agent_name,
        "evaluation_date": report.evaluation_date,
        "total_tasks": report.total_tasks,
        "overall_score": report.overall_score,
        "score_by_difficulty": report.score_by_difficulty,
        "strengths": report.strengths,
        "weaknesses": report.weaknesses,
        "recommendations": report.recommendations,
        "task_results": [
            {
                "task_id": r.task_id,
                "difficulty": r.difficulty,
                "final_score": r.final_score,
                "steps_taken": r.steps_taken,
                "errors": r.errors,
                "duration_seconds": r.duration_seconds,
            }
            for r in report.task_results
        ],
        "raw_data": report.raw_data,
    }

    with open(filepath, "w") as f:
        json.dump(report_dict, f, indent=2)

    return str(filepath)


def print_report(report: EvaluationReport) -> None:
    """Print human-readable report."""
    print("\n" + "=" * 70)
    print(f"EVALUATION REPORT: {report.agent_name}")
    print(f"Agent ID: {report.agent_id}")
    print(f"Date: {report.evaluation_date}")
    print("=" * 70)

    print(f"\n📊 OVERALL SCORE: {report.overall_score:.2%}")
    print(f"   Tasks Evaluated: {report.total_tasks}")

    print("\n📈 SCORE BY DIFFICULTY:")
    for difficulty, score in sorted(report.score_by_difficulty.items()):
        bar = "█" * int(score * 20)
        print(f"   {difficulty:10s}: {score:.2%} {bar}")

    print("\n✅ STRENGTHS:")
    for strength in report.strengths:
        print(f"   • {strength}")

    print("\n⚠️  WEAKNESSES:")
    for weakness in report.weaknesses:
        print(f"   • {weakness}")

    print("\n💡 RECOMMENDATIONS:")
    for rec in report.recommendations:
        print(f"   • {rec}")

    print("\n📋 TASK DETAILS:")
    for result in report.task_results:
        status = "✅" if result.final_score > 0.7 else "⚠️" if result.final_score > 0.4 else "❌"
        print(f"   {status} {result.task_id:25s} | Score: {result.final_score:.2%} | Steps: {result.steps_taken:2d} | Errors: {result.errors}")

    print("\n" + "=" * 70)


def main() -> None:
    """Run evaluation-as-a-service."""
    validate_environment()
    
    # Get agent info from env vars or defaults
    agent_id = os.getenv("AGENT_ID", "agent_001")
    agent_name = os.getenv("AGENT_NAME", "Default Agent")
    env_base_url = os.getenv("ENV_BASE_URL", "http://127.0.0.1:8000")

    print(f"Starting evaluation for {agent_name} ({agent_id})")
    
    client = get_openai_client()
    
    # Fetch available tasks
    with GenericEnvClient(base_url=env_base_url).sync() as env:
        result = env.reset()
        task_ids = [task["task_id"] for task in result.observation.get("available_tasks", [])]
    
    print(f"Found {len(task_ids)} tasks to evaluate")

    # Run evaluations
    task_results = []
    for task_id in task_ids:
        print(f"\nEvaluating {task_id}...")
        result = run_single_task(client, task_id, env_base_url=env_base_url)
        task_results.append(result)
        print(f"  Score: {result.final_score:.2%} | Steps: {result.steps_taken} | Errors: {result.errors}")

    # Generate report
    report = generate_report(agent_id, agent_name, task_results)
    
    # Print and save
    print_report(report)
    report_path = save_report(report)
    print(f"\n📄 Report saved to: {report_path}")


if __name__ == "__main__":
    main()
