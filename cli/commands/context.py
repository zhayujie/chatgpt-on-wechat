"""cow context - Context management commands."""

import os
import sys
import json
import glob as glob_mod

import click

from cli.utils import get_workspace_dir


@click.group(invoke_without_command=True)
@click.pass_context
def context(ctx):
    """View or manage conversation context.

    Without a subcommand, shows context info for the current workspace.
    """
    if ctx.invoked_subcommand is None:
        _show_context_info()


@context.command()
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def clear(yes):
    """Clear conversation context (messages history)."""
    workspace = get_workspace_dir()
    sessions_dir = os.path.join(workspace, "sessions")

    if not os.path.isdir(sessions_dir):
        click.echo("No conversation data found.")
        return

    db_files = glob_mod.glob(os.path.join(sessions_dir, "*.db"))
    if not db_files:
        click.echo("No conversation data found.")
        return

    if not yes:
        click.confirm("Clear all conversation context? This cannot be undone.", abort=True)

    removed = 0
    for db_file in db_files:
        try:
            os.remove(db_file)
            removed += 1
        except Exception as e:
            click.echo(f"Warning: Failed to remove {db_file}: {e}", err=True)

    click.echo(click.style(f"✓ Cleared {removed} conversation database(s).", fg="green"))


def _show_context_info():
    """Display conversation context status."""
    workspace = get_workspace_dir()
    sessions_dir = os.path.join(workspace, "sessions")

    click.echo(f"\n  Context info")
    click.echo(f"  Workspace: {workspace}")

    if not os.path.isdir(sessions_dir):
        click.echo("  Sessions: none\n")
        return

    db_files = glob_mod.glob(os.path.join(sessions_dir, "*.db"))
    total_size = sum(os.path.getsize(f) for f in db_files if os.path.exists(f))

    click.echo(f"  Sessions dir: {sessions_dir}")
    click.echo(f"  Database files: {len(db_files)}")
    click.echo(f"  Total size: {_format_size(total_size)}")
    click.echo(f"\n  Use 'cow context clear' to reset.\n")


def _format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
