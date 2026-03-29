"""CLI utility functions — shared helpers for prellm CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer


def _init_logging() -> None:
    """Initialize nfo logging from .env config (called once per CLI invocation)."""
    from prellm.env_config import get_env_config
    from prellm.logging_setup import setup_logging

    env = get_env_config()
    setup_logging(level=env.log_level)


def _handle_query_options(
    prompt: str,
    small: Optional[str],
    large: Optional[str],
    strategy: Optional[str],
    context: Optional[str],
    config: Optional[Path],
    memory: Optional[Path],
    codebase: Optional[Path],
    collect_env: bool,
    compress_folder: Optional[Path],
    no_sanitize: bool,
    show_schema: bool,
    show_blocked: bool,
    json_output: bool,
    trace: bool,
    trace_dir: Optional[Path],
    env_file: Optional[Path],
) -> dict:
    """Process and validate CLI query options."""
    from prellm.env_config import get_env_config

    env = get_env_config(str(env_file) if env_file else None)
    effective_small = small or env.small_model
    effective_large = large or env.large_model
    effective_strategy = strategy or env.strategy

    effective_codebase = str(codebase) if codebase else (str(compress_folder) if compress_folder else None)
    do_sanitize = not no_sanitize
    do_compress = compress_folder is not None

    return {
        "prompt": prompt,
        "small_llm": effective_small,
        "large_llm": effective_large,
        "strategy": effective_strategy,
        "user_context": context,
        "config_path": str(config) if config else None,
        "memory_path": str(memory) if memory else None,
        "codebase_path": effective_codebase,
        "collect_env": collect_env,
        "compress_folder": do_compress,
        "sanitize": do_sanitize,
        "trace": trace,
        "trace_dir": trace_dir,
        "json_output": json_output,
        "show_schema": show_schema,
        "show_blocked": show_blocked,
        "compress_folder_path": compress_folder,
        "env": env,
    }


def _show_debug_info(options: dict) -> None:
    """Show schema and blocked sensitive fields if requested."""
    collect_env = options["collect_env"]
    compress_folder = options["compress_folder_path"]
    show_schema = options["show_schema"]
    show_blocked = options["show_blocked"]
    do_compress = options["compress_folder"]

    # Show schema before execution if requested
    if show_schema and (collect_env or do_compress):
        from prellm.context.shell_collector import ShellContextCollector
        from prellm.context.schema_generator import ContextSchemaGenerator
        from prellm.context.folder_compressor import FolderCompressor

        shell_ctx = ShellContextCollector().collect_all() if collect_env else None
        compressed = FolderCompressor().compress(compress_folder) if compress_folder else None
        schema = ContextSchemaGenerator().generate(shell_context=shell_ctx, folder_compressed=compressed)
        typer.echo(f"\n📋 Context Schema:")
        typer.echo(schema.model_dump_json(indent=2))
        typer.echo("")

    # Show blocked fields if requested
    if show_blocked and collect_env:
        from prellm.context.shell_collector import ShellContextCollector
        from prellm.context.sensitive_filter import SensitiveDataFilter

        collector = ShellContextCollector()
        all_vars = collector.collect_env_vars(safe_only=False)
        filt = SensitiveDataFilter()
        filt.filter_dict(all_vars)
        report = filt.get_filter_report()
        typer.echo(f"\n🔒 Sensitive Filter Report:")
        typer.echo(f"   Blocked:  {len(report.blocked_keys)} — {', '.join(report.blocked_keys[:10])}")
        typer.echo(f"   Masked:   {len(report.masked_keys)} — {', '.join(report.masked_keys[:10])}")
        typer.echo(f"   Safe:     {len(report.safe_keys)}")
        typer.echo("")


def _initialize_execution(options: dict) -> Optional["TraceRecorder"]:
    """Initialize budget tracker and trace recorder."""
    from prellm.trace import TraceRecorder
    from prellm.budget import get_budget_tracker

    env = options["env"]
    trace = options["trace"]
    trace_dir = options["trace_dir"]

    # Initialize budget tracker if configured
    if env.monthly_budget:
        get_budget_tracker(monthly_limit=env.monthly_budget)

    # Start trace if requested
    recorder = None
    if trace:
        recorder = TraceRecorder(output_dir=Path(trace_dir) if trace_dir else Path(".prellm"))
        recorder.start(
            query=options["prompt"],
            small_llm=options["small_llm"],
            large_llm=options["large_llm"],
            strategy=options["strategy"],
        )

    return recorder


def _execute_and_format_result(options: dict, recorder: Optional["TraceRecorder"]) -> None:
    """Execute the query and format output."""
    import asyncio
    from prellm.core import preprocess_and_execute

    result = asyncio.run(preprocess_and_execute(
        query=options["prompt"],
        small_llm=options["small_llm"],
        large_llm=options["large_llm"],
        strategy=options["strategy"],
        user_context=options["user_context"],
        config_path=options["config_path"],
        memory_path=options["memory_path"],
        codebase_path=options["codebase_path"],
        collect_env=options["collect_env"],
        compress_folder=options["compress_folder"],
        sanitize=options["sanitize"],
    ))

    # Stop trace and output
    if recorder:
        recorder.stop()
        typer.echo(recorder.to_stdout())
        filepath = recorder.save()
        typer.echo(f"📄 Trace saved: {filepath}")

    if options["json_output"]:
        typer.echo(result.model_dump_json(indent=2))
    else:
        typer.echo(f"\n{'='*60}")
        typer.echo(f"🧠 preLLM [{options['small_llm']} → {options['large_llm']}]")
        typer.echo(f"{'='*60}")
        if result.decomposition and result.decomposition.classification:
            c = result.decomposition.classification
            typer.echo(f"   Intent: {c.intent} (confidence: {c.confidence:.2f})")
        if result.decomposition and result.decomposition.matched_rule:
            typer.echo(f"   Rule: {result.decomposition.matched_rule}")
        if result.decomposition and result.decomposition.missing_fields:
            typer.echo(f"   ⚠️  Missing: {', '.join(result.decomposition.missing_fields)}")
        typer.echo(f"{'='*60}")
        typer.echo(f"\n{result.content}")
        typer.echo(f"\n{'='*60}")
        typer.echo(f"   Small: {result.small_model_used} | Large: {result.model_used} | Retries: {result.retries}")
        typer.echo(f"{'='*60}")
