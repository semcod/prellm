"""Budget command — LLM API spend tracking and budget status."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer


def budget_cmd(
    reset: bool = typer.Option(False, "--reset", help="Reset current month's budget"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show LLM API spend tracking and budget status."""
    from prellm.budget import get_budget_tracker
    from prellm.env_config import get_env_config
    from prellm.cli.utils import _init_logging

    _init_logging()
    env = get_env_config()
    tracker = get_budget_tracker(monthly_limit=env.monthly_budget)

    if reset:
        tracker.reset()
        typer.echo("✅ Budget reset for current month.")
        return

    summary = tracker.summary()

    if json_output:
        typer.echo(json.dumps(summary, indent=2, default=str))
        return

    typer.echo(f"\n💰 preLLM Budget")
    typer.echo(f"{'='*60}")
    typer.echo(f"   Month:      {summary['month']}")
    typer.echo(f"   Spent:      ${summary['total_cost']:.4f}")
    if summary['monthly_limit'] is not None:
        typer.echo(f"   Limit:      ${summary['monthly_limit']:.2f}")
        typer.echo(f"   Remaining:  ${summary['remaining']:.4f}")
        pct = (summary['total_cost'] / summary['monthly_limit'] * 100) if summary['monthly_limit'] > 0 else 0
        bar_len = 30
        filled = int(bar_len * min(pct, 100) / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        typer.echo(f"   Usage:      [{bar}] {pct:.1f}%")
    else:
        typer.echo(f"   Limit:      not set (PRELLM_MONTHLY_BUDGET)")
    typer.echo(f"   Requests:   {summary['requests']}")

    if summary['by_model']:
        typer.echo(f"\n   By model:")
        for model, cost in sorted(summary['by_model'].items(), key=lambda x: -x[1]):
            typer.echo(f"     {model}: ${cost:.4f}")

    typer.echo(f"\n{'='*60}")
