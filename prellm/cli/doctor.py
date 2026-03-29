"""Doctor command — configuration and provider health checks."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer


def _doctor_check_config(env) -> list[str]:
    """Format configuration summary lines."""
    lines = [
        f"   Small LLM:  {env.small_model}",
        f"   Large LLM:  {env.large_model}",
        f"   Strategy:   {env.strategy}",
        f"   Server:     {env.host}:{env.port}",
        f"   Auth:       {'ON' if env.master_key else 'OFF (no LITELLM_MASTER_KEY)'}",
    ]
    if env.config_path:
        lines.append(f"   Config:     {env.config_path}")
    if env.fallbacks:
        lines.append(f"   Fallbacks:  {', '.join(env.fallbacks)}")
    if env.monthly_budget:
        lines.append(f"   Budget:     ${env.monthly_budget:.2f}/month")
    return lines


def _doctor_check_providers(env, live: bool = False) -> list[str]:
    """Check providers and return formatted lines."""
    from prellm.env_config import check_providers

    if live:
        import asyncio
        from prellm.env_config import check_providers_live
        results = asyncio.run(check_providers_live(env))
    else:
        results = check_providers(env)

    lines = []
    for name, info in results.items():
        status = info["status"]
        icon = "✓" if status in ("ok", "configured") else ("✗" if status == "no_key" else "!")
        lines.append(f"   {icon} {name.upper():12s} {info['detail']}")
        if "models" in info:
            lines.append(f"     Models: {', '.join(info['models'][:5])}")
    return lines


def _doctor_check_files(env_file: Path | None) -> list[str]:
    """Check config files and return formatted lines."""
    lines = []
    env_path = Path(str(env_file)) if env_file else Path(".env")
    if env_path.is_file():
        lines.append(f"   ✓ {env_path} (loaded)")
    else:
        lines.append(f"   ✗ {env_path} (not found — run: cp .env.example .env)")

    example_path = Path(".env.example")
    if example_path.is_file():
        lines.append(f"   ✓ .env.example (available)")
    else:
        lines.append(f"   ✗ .env.example (not found)")

    config_yaml = Path("configs/prellm_config.yaml")
    if config_yaml.is_file():
        lines.append(f"   ✓ {config_yaml}")
    return lines


def doctor_cmd(
    env_file: Optional[Path] = typer.Option(None, "--env-file", help="Path to .env file"),
    live: bool = typer.Option(False, "--live", help="Test live connectivity to providers"),
) -> None:
    """Check configuration and provider connectivity."""
    from prellm.env_config import get_env_config
    from prellm.cli.utils import _init_logging

    _init_logging()
    env = get_env_config(str(env_file) if env_file else None)

    typer.echo(f"\n🧠 preLLM Doctor")
    typer.echo(f"{'='*60}")

    typer.echo(f"\n📋 Configuration:")
    for line in _doctor_check_config(env):
        typer.echo(line)

    typer.echo(f"\n🔌 Providers:")
    for line in _doctor_check_providers(env, live=live):
        typer.echo(line)

    typer.echo(f"\n📄 Files:")
    for line in _doctor_check_files(env_file):
        typer.echo(line)

    typer.echo(f"\n{'='*60}")
    typer.echo(f"✅ Doctor complete. Use --live to test connectivity.\n")
