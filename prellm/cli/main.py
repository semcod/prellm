"""preLLM CLI main module — entry point and command registration."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from prellm.cli.utils import (
    _handle_query_options,
    _show_debug_info,
    _initialize_execution,
    _execute_and_format_result,
    _init_logging,
)

# Main CLI app
app = typer.Typer(
    name="prellm",
    help="preLLM — Small LLM preprocessing before large LLM execution. Like litellm.completion() but with decomposition.",
    no_args_is_help=True,
)


# ============================================================
# Main query command
# ============================================================

@app.command()
def query(
    prompt: str = typer.Argument(..., help="The prompt/query to preprocess and execute"),
    small: Optional[str] = typer.Option(None, "--small", "-s", help="Small LLM for preprocessing (default: from .env)"),
    large: Optional[str] = typer.Option(None, "--large", "-l", help="Large LLM for execution (default: from .env)"),
    strategy: Optional[str] = typer.Option(None, "--strategy", "-S", help="Strategy: classify|structure|split|enrich|passthrough (default: from .env)"),
    context: Optional[str] = typer.Option(None, "--context", "-C", help="User context tag (e.g. 'gdansk_embedded_python')"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Optional YAML config file"),
    memory: Optional[Path] = typer.Option(None, "--memory", "-m", help="Path to UserMemory database"),
    codebase: Optional[Path] = typer.Option(None, "--codebase", help="Path to codebase root for context indexing"),
    collect_env: bool = typer.Option(False, "--collect-env", help="Collect full shell environment context"),
    compress_folder: Optional[Path] = typer.Option(None, "--compress-folder", help="Compress folder for context (path)"),
    no_sanitize: bool = typer.Option(False, "--no-sanitize", help="Disable sensitive data filtering (dev only)"),
    show_schema: bool = typer.Option(False, "--show-schema", help="Show generated context schema (debug)"),
    show_blocked: bool = typer.Option(False, "--show-blocked", help="Show blocked sensitive fields"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    trace: bool = typer.Option(False, "--trace", "-t", help="Generate markdown execution trace (.prellm/)"),
    trace_dir: Optional[Path] = typer.Option(None, "--trace-dir", help="Trace output directory (default: .prellm)"),
    env_file: Optional[Path] = typer.Option(None, "--env-file", help="Path to .env file (default: .env)"),
):
    """Preprocess a query with small LLM, then execute with large LLM."""
    _init_logging()

    options = _handle_query_options(
        prompt, small, large, strategy, context, config, memory, codebase,
        collect_env, compress_folder, no_sanitize, show_schema, show_blocked,
        json_output, trace, trace_dir, env_file
    )

    _show_debug_info(options)

    recorder = _initialize_execution(options)

    _execute_and_format_result(options, recorder)


# ============================================================
# Register sub-apps
# ============================================================

from prellm.cli.context import context_shell_cmd
from prellm.cli.process import process_cmd, decompose_cmd, init_cmd
from prellm.cli.doctor import doctor_cmd
from prellm.cli.config import (
    config_set_cmd,
    config_get_cmd,
    config_list_cmd,
    config_show_cmd,
    config_init_env,
)
from prellm.cli.budget import budget_cmd
from prellm.cli.models import models_cmd
from prellm.cli.context import context_show_cmd
from prellm.cli.session import (
    session_list_cmd,
    session_export_cmd,
    session_import_cmd,
    session_clear_cmd,
)

# Context command (legacy single command)
app.command(name="context")(context_shell_cmd)

# Process commands
app.command(name="process")(process_cmd)
app.command(name="decompose")(decompose_cmd)
app.command(name="init")(init_cmd)

# Doctor
app.command(name="doctor")(doctor_cmd)

# Budget
app.command(name="budget")(budget_cmd)

# Models
app.command(name="models")(models_cmd)


# ============================================================
# Config sub-app
# ============================================================

config_app = typer.Typer(
    name="config",
    help="Manage preLLM configuration — API keys, models, defaults.",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")

config_app.command("set")(config_set_cmd)
config_app.command("get")(config_get_cmd)
config_app.command("list")(config_list_cmd)
config_app.command("show")(config_show_cmd)
config_app.command("init-env")(config_init_env)


# ============================================================
# Context inspection sub-app
# ============================================================

context_app = typer.Typer(
    name="context",
    help="Inspect runtime context — env vars, process, locale, network, codebase.",
    no_args_is_help=True,
)
app.add_typer(context_app, name="context")

context_app.command("show")(context_show_cmd)


# ============================================================
# Session management sub-app
# ============================================================

session_app = typer.Typer(
    name="session",
    help="Manage persistent sessions — export, import, list, clear.",
    no_args_is_help=True,
)
app.add_typer(session_app, name="session")

session_app.command("list")(session_list_cmd)
session_app.command("export")(session_export_cmd)
session_app.command("import")(session_import_cmd)
session_app.command("clear")(session_clear_cmd)


# ============================================================
# Server command
# ============================================================

@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-H", help="Bind host"),
    port: int = typer.Option(8080, "--port", "-p", help="Bind port"),
    small: Optional[str] = typer.Option(None, "--small", "-s", help="Override small LLM (default: from .env)"),
    large: Optional[str] = typer.Option(None, "--large", "-l", help="Override large LLM (default: from .env)"),
    strategy: Optional[str] = typer.Option(None, "--strategy", "-S", help="Override strategy (default: from .env)"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="YAML config file"),
    env_file: Optional[Path] = typer.Option(None, "--env-file", help="Path to .env file (default: .env)"),
    reload: bool = typer.Option(False, "--reload", help="Auto-reload on code changes (dev mode)"),
):
    """Start the OpenAI-compatible API server."""
    import uvicorn
    from prellm.env_config import get_env_config
    from prellm.server import create_app

    env = get_env_config(str(env_file) if env_file else None)
    _init_logging()

    effective_small = small or env.small_model
    effective_large = large or env.large_model
    effective_strategy = strategy or env.strategy

    create_app(
        small_model=effective_small,
        large_model=effective_large,
        strategy=effective_strategy,
        config_path=str(config) if config else env.config_path,
        dotenv_path=str(env_file) if env_file else None,
    )

    auth_status = "ON (LITELLM_MASTER_KEY)" if env.master_key else "OFF (no key set)"

    typer.echo(f"\n🧠 preLLM API Server")
    typer.echo(f"   http://host}:{port}")
    typer.echo(f"   Small: {effective_small} | Large: {effective_large}")
    typer.echo(f"   Strategy: {effective_strategy} | Auth: {auth_status}")
    typer.echo(f"   Endpoints: /v1/chat/completions, /v1/batch, /v1/models, /health")
    typer.echo(f"{'='*60}\n")

    uvicorn.run(
        "prellm.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level=env.log_level,
    )


if __name__ == "__main__":
    app()
