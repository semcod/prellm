"""Context commands — environment context inspection."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer


def context_show_cmd(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    blocked: bool = typer.Option(False, "--blocked", help="Show what was blocked by sensitive filter"),
    codebase: Optional[Path] = typer.Option(None, "--codebase", help="Show compressed codebase context"),
) -> None:
    """Show collected runtime context."""
    from prellm.analyzers.context_engine import ContextEngine
    from prellm.cli.utils import _init_logging

    _init_logging()
    engine = ContextEngine()
    runtime = engine.gather_runtime()

    if json_output:
        typer.echo(runtime.model_dump_json(indent=2))
        return

    typer.echo(f"\n🧠 preLLM Runtime Context")
    typer.echo(f"{'='*60}")
    typer.echo(f"   Collected at: {runtime.collected_at}")
    typer.echo(f"   Token estimate: {runtime.token_estimate}")
    typer.echo(f"   Sensitive blocked: {runtime.sensitive_blocked_count}")

    typer.echo(f"\n💻 Process:")
    for k, v in runtime.process.items():
        typer.echo(f"   {k}: {v}")

    typer.echo(f"\n🌍 Locale:")
    for k, v in runtime.locale.items():
        typer.echo(f"   {k}: {v}")

    typer.echo(f"\n🌐 Network:")
    for k, v in runtime.network.items():
        typer.echo(f"   {k}: {v}")

    typer.echo(f"\n⚙️  System:")
    for k, v in runtime.system.items():
        typer.echo(f"   {k}: {v}")

    if runtime.git:
        typer.echo(f"\n🔀 Git:")
        for k, v in runtime.git.items():
            typer.echo(f"   {k}: {v}")

    typer.echo(f"\n🔒 Safe env vars: {len(runtime.env_safe)}")
    if blocked:
        typer.echo(f"   (showing first 20)")
        for i, (k, v) in enumerate(runtime.env_safe.items()):
            if i >= 20:
                typer.echo(f"   ... and {len(runtime.env_safe) - 20} more")
                break
            typer.echo(f"   {k}={v[:60]}{'...' if len(v) > 60 else ''}")

    if codebase:
        from prellm.context.codebase_indexer import CodebaseIndexer
        indexer = CodebaseIndexer()
        compressed = indexer.get_compressed_context(str(codebase), "project overview", max_tokens=2048)
        typer.echo(f"\n📂 Codebase ({codebase}):")
        typer.echo(compressed)

    typer.echo(f"\n{'='*60}")


def context_shell_cmd(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    schema: bool = typer.Option(False, "--schema", help="Show generated context schema"),
    blocked: bool = typer.Option(False, "--blocked", help="Show blocked sensitive data"),
    folder: Optional[Path] = typer.Option(None, "--folder", "-f", help="Folder to compress for context"),
) -> None:
    """Show collected environment context, schema, and blocked sensitive data."""
    from prellm.context.shell_collector import ShellContextCollector
    from prellm.context.schema_generator import ContextSchemaGenerator
    from prellm.context.sensitive_filter import SensitiveDataFilter

    collector = ShellContextCollector()
    shell_ctx = collector.collect_all()

    if json_output and not schema and not blocked:
        typer.echo(shell_ctx.model_dump_json(indent=2))
        return

    if schema:
        compressed = None
        if folder:
            from prellm.context.folder_compressor import FolderCompressor
            compressed = FolderCompressor().compress(folder)
        gen = ContextSchemaGenerator()
        ctx_schema = gen.generate(shell_context=shell_ctx, folder_compressed=compressed)
        if json_output:
            typer.echo(ctx_schema.model_dump_json(indent=2))
        else:
            typer.echo(f"\n📋 Context Schema:")
            typer.echo(gen.to_prompt_section(ctx_schema))
            typer.echo(f"\n   Token cost: ~{ctx_schema.schema_token_cost}")
        return

    if blocked:
        all_vars = collector.collect_env_vars(safe_only=False)
        filt = SensitiveDataFilter()
        filt.filter_dict(all_vars)
        report = filt.get_filter_report()
        if json_output:
            typer.echo(report.model_dump_json(indent=2))
        else:
            typer.echo(f"\n🔒 Sensitive Filter Report:")
            typer.echo(f"   Blocked ({len(report.blocked_keys)}): {', '.join(report.blocked_keys[:15])}")
            typer.echo(f"   Masked  ({len(report.masked_keys)}): {', '.join(report.masked_keys[:15])}")
            typer.echo(f"   Safe    ({len(report.safe_keys)}): {len(report.safe_keys)} keys")
        return

    # Default: show shell context summary
    typer.echo(f"\n🧠 preLLM Environment Context")
    typer.echo(f"{'='*60}")
    typer.echo(f"   PID:      {shell_ctx.process.pid}")
    typer.echo(f"   CWD:      {shell_ctx.process.cwd}")
    typer.echo(f"   User:     {shell_ctx.process.user}")
    typer.echo(f"   Shell:    {shell_ctx.shell.shell}")
    typer.echo(f"   Term:     {shell_ctx.shell.term}")
    typer.echo(f"   Locale:   {shell_ctx.locale.lang}")
    typer.echo(f"   Timezone: {shell_ctx.locale.timezone}")
    typer.echo(f"   Hostname: {shell_ctx.network.hostname}")
    typer.echo(f"   Local IP: {shell_ctx.network.local_ip}")
    typer.echo(f"   Env vars: {len(shell_ctx.env_vars)} (safe only)")
    typer.echo(f"   Collected in: {shell_ctx.collection_duration_ms:.1f}ms")
    typer.echo(f"{'='*60}")
