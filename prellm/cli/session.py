"""Session commands — manage persistent sessions."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer


def session_list_cmd(
    memory: Path = Path(".prellm/user_memory.db"),
) -> None:
    """List recent interactions in the session."""
    from prellm.context.user_memory import UserMemory
    from prellm.cli.utils import _init_logging

    _init_logging()
    mem = UserMemory(path=str(memory))
    try:
        interactions = asyncio.run(mem._get_all_interactions(limit=20))
        if not interactions:
            typer.echo("No interactions found.")
            return
        typer.echo(f"\n💬 Session ({memory}): {len(interactions)} interactions")
        typer.echo(f"{'='*60}")
        for i, item in enumerate(interactions, 1):
            q = item.get("query", "")[:80]
            r = item.get("response_summary", "")[:60]
            typer.echo(f"   {i}. Q: {q}")
            typer.echo(f"      A: {r}...")
        typer.echo(f"{'='*60}")
    finally:
        mem.close()


def session_export_cmd(
    output: Path,
    memory: Path = Path(".prellm/user_memory.db"),
    session_id: Optional[str] = None,
) -> None:
    """Export current session to JSON file."""
    from prellm.context.user_memory import UserMemory
    from prellm.cli.utils import _init_logging

    _init_logging()
    mem = UserMemory(path=str(memory))
    try:
        snapshot = asyncio.run(mem.export_session(session_id=session_id))
        snapshot.to_file(output)
        typer.echo(f"✅ Session exported to {output}")
        typer.echo(f"   ID: {snapshot.session_id}")
        typer.echo(f"   Interactions: {len(snapshot.interactions)}")
        typer.echo(f"   Preferences: {len(snapshot.preferences)}")
    finally:
        mem.close()


def session_import_cmd(
    input_file: Path,
    memory: Path = Path(".prellm/user_memory.db"),
) -> None:
    """Import a session from JSON file."""
    from prellm.context.user_memory import UserMemory
    from prellm.models import SessionSnapshot
    from prellm.cli.utils import _init_logging

    _init_logging()
    snapshot = SessionSnapshot.from_file(input_file)
    mem = UserMemory(path=str(memory))
    try:
        asyncio.run(mem.import_session(snapshot))
        typer.echo(f"✅ Session imported from {input_file}")
        typer.echo(f"   ID: {snapshot.session_id}")
        typer.echo(f"   Interactions: {len(snapshot.interactions)}")
    finally:
        mem.close()


def session_clear_cmd(
    memory: Path = Path(".prellm/user_memory.db"),
    force: bool = False,
) -> None:
    """Clear all session data."""
    from prellm.context.user_memory import UserMemory
    from prellm.cli.utils import _init_logging

    if not force:
        typer.confirm("This will delete all session data. Continue?", abort=True)

    _init_logging()
    mem = UserMemory(path=str(memory))
    try:
        asyncio.run(mem.clear())
        typer.echo(f"✅ Session cleared ({memory})")
    finally:
        mem.close()
