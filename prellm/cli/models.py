"""Models command — list popular model pairs and provider examples."""

from __future__ import annotations

from typing import Optional

import typer


def models_cmd(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search model name"),
) -> None:
    """List popular model pairs and provider examples."""
    from prellm.model_catalog import list_model_pairs, list_openrouter_models

    pairs = list_model_pairs(provider=provider, search=search)
    or_models = list_openrouter_models(provider=provider, search=search)

    typer.echo(f"\n🤖 preLLM Model Pairs")
    typer.echo(f"{'='*60}")

    if pairs:
        typer.echo(f"\n{'Name':<25s} {'Small LLM':<30s} {'Large LLM':<45s} {'Cost':>6s}")
        typer.echo(f"{'-'*25} {'-'*30} {'-'*45} {'-'*6}")
        for m in pairs:
            typer.echo(f"{m['name']:<25s} {m['small']:<30s} {m['large']:<45s} {m['cost']:>6s}")

    if or_models:
        typer.echo(f"\n🌐 OpenRouter Models (use with --large):")
        for m in or_models:
            typer.echo(f"   {m['model_id']}")
            typer.echo(f"      {m['description']}")

    typer.echo(f"\n💡 Usage:")
    typer.echo(f'   prellm "Deploy app" --large openrouter/moonshotai/kimi-k2.5')
    typer.echo(f"   prellm config set model openrouter/moonshotai/kimi-k2.5")
    typer.echo(f"   prellm config set openrouter-key sk-or-v1-abc123")
    typer.echo(f"\n{'='*60}")
