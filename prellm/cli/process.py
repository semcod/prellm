"""Process command — execute DevOps process chains."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer


def process_cmd(
    config: Path,
    guard_config: Path = Path("rules.yaml"),
    dry_run: bool = False,
    json_output: bool = False,
    env: Optional[str] = None,
) -> None:
    """Execute a DevOps process chain."""
    from prellm.chains.process_chain import ProcessChain

    chain = ProcessChain(config_path=config, guard_config_path=guard_config)

    extra = {}
    if env:
        extra["env"] = env

    result = asyncio.run(chain.execute(extra_context=extra, dry_run=dry_run))

    if json_output:
        typer.echo(result.model_dump_json(indent=2))
    else:
        typer.echo(f"\n{'='*60}")
        typer.echo(f"🔗 Process: {result.process_name}")
        typer.echo(f"   Status: {'✅ Completed' if result.completed else '⏸️  Incomplete'}")
        typer.echo(f"   Duration: {result.total_duration_seconds:.2f}s")
        typer.echo(f"{'='*60}")
        for step in result.steps:
            icon = {
                "completed": "✅",
                "failed": "❌",
                "awaiting_approval": "⏳",
                "rolled_back": "↩️",
            }.get(step.status.value, "🔄")
            typer.echo(f"   {icon} {step.step_name}: {step.status.value} ({step.duration_seconds:.2f}s)")
            if step.error:
                typer.echo(f"      Error: {step.error}")
        typer.echo(f"{'='*60}")


def decompose_cmd(
    query: str,
    config: Path = Path("configs/prellm_config.yaml"),
    strategy: str = "classify",
    json_output: bool = False,
) -> None:
    """Decompose a query using small LLM without calling the large model."""
    from prellm.core import PreLLM
    from prellm.models import DecompositionStrategy

    engine = PreLLM(config_path=config)
    strat = DecompositionStrategy(strategy)

    result = asyncio.run(engine.decompose_only(query, strategy=strat))

    if json_output:
        import json
        typer.echo(json.dumps(result, indent=2, default=str))
    else:
        typer.echo(f"\n{'='*60}")
        typer.echo(f"🧠 preLLM Decomposition [{strategy}]")
        typer.echo(f"{'='*60}")
        typer.echo(f"   Original: {result['original_query']}")
        if result.get('classification'):
            c = result['classification']
            typer.echo(f"   Intent: {c['intent']} (confidence: {c['confidence']:.2f})")
            typer.echo(f"   Domain: {c['domain']}")
        if result.get('structure'):
            s = result['structure']
            typer.echo(f"   Action: {s['action']}, Target: {s['target']}")
        if result.get('sub_queries'):
            typer.echo(f"   Sub-queries: {result['sub_queries']}")
        if result.get('missing_fields'):
            typer.echo(f"   ⚠️  Missing: {', '.join(result['missing_fields'])}")
        if result.get('matched_rule'):
            typer.echo(f"   Matched rule: {result['matched_rule']}")
        typer.echo(f"   Composed: {result.get('composed_prompt', '')[:200]}")
        typer.echo(f"{'='*60}")


def init_cmd(
    output: Path = Path("prellm_config.yaml"),
    devops: bool = False,
) -> None:
    """Generate a starter preLLM config file."""
    import yaml

    config = {
        "small_model": {"model": "phi3:mini", "fallback": ["qwen2:1.5b"], "max_tokens": 512, "temperature": 0.0},
        "large_model": {"model": "gpt-4o-mini", "fallback": ["llama3"], "max_tokens": 2048},
        "default_strategy": "classify",
        "policy": "devops" if devops else "strict",
        "domain_rules": [
            {"name": "production_deploy", "keywords": ["deploy", "push", "release"],
             "intent": "deploy", "required_fields": ["environment_details", "version"],
             "severity": "critical", "strategy": "structure"},
            {"name": "database_operation", "keywords": ["delete", "drop", "migrate"],
             "intent": "database", "required_fields": ["target_database", "backup_confirmed"],
             "severity": "critical", "strategy": "structure"},
        ] if devops else [],
        "context_sources": [
            {"env": ["CLUSTER", "NAMESPACE", "GIT_SHA", "ENV"]},
            {"git": ["branch", "short_sha", "last_commit_msg"]},
            {"system": ["hostname", "os"]},
        ] if devops else [],
    }

    with open(output, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    typer.echo(f"✅ Config written to {output}")
