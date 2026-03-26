"""cow start/stop/restart/status/logs - Process management commands."""

import os
import sys
import signal
import subprocess
import time
from typing import Optional

import click

from cli.utils import get_project_root


def _get_pid_file():
    return os.path.join(get_project_root(), ".cow.pid")


def _get_log_file():
    return os.path.join(get_project_root(), "nohup.out")


def _read_pid() -> Optional[int]:
    pid_file = _get_pid_file()
    if not os.path.exists(pid_file):
        return None
    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return pid
    except (ValueError, ProcessLookupError, PermissionError):
        os.remove(pid_file)
        return None


def _write_pid(pid: int):
    with open(_get_pid_file(), "w") as f:
        f.write(str(pid))


def _remove_pid():
    pid_file = _get_pid_file()
    if os.path.exists(pid_file):
        os.remove(pid_file)


@click.command()
@click.option("--foreground", "-f", is_flag=True, help="Run in foreground (don't daemonize)")
def start(foreground):
    """Start CowAgent."""
    pid = _read_pid()
    if pid:
        click.echo(f"CowAgent is already running (PID: {pid}).")
        return

    root = get_project_root()
    app_py = os.path.join(root, "app.py")
    if not os.path.exists(app_py):
        click.echo("Error: app.py not found in project root.", err=True)
        sys.exit(1)

    python = sys.executable

    if foreground:
        click.echo("Starting CowAgent in foreground...")
        os.execv(python, [python, app_py])
    else:
        log_file = _get_log_file()
        click.echo("Starting CowAgent...")

        with open(log_file, "a") as log:
            proc = subprocess.Popen(
                [python, app_py],
                cwd=root,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
        _write_pid(proc.pid)
        click.echo(click.style(f"✓ CowAgent started (PID: {proc.pid})", fg="green"))
        click.echo(f"  Logs: {log_file}")


@click.command()
def stop():
    """Stop CowAgent."""
    pid = _read_pid()
    if not pid:
        click.echo("CowAgent is not running.")
        return

    click.echo(f"Stopping CowAgent (PID: {pid})...")
    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(30):
            time.sleep(0.1)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
        else:
            os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass

    _remove_pid()
    click.echo(click.style("✓ CowAgent stopped.", fg="green"))


@click.command()
@click.pass_context
def restart(ctx):
    """Restart CowAgent."""
    ctx.invoke(stop)
    time.sleep(1)
    ctx.invoke(start)


@click.command()
def status():
    """Show CowAgent running status."""
    pid = _read_pid()
    if pid:
        click.echo(click.style(f"● CowAgent is running (PID: {pid})", fg="green"))
    else:
        click.echo(click.style("● CowAgent is not running", fg="red"))


@click.command()
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option("--lines", "-n", default=50, help="Number of lines to show")
def logs(follow, lines):
    """View CowAgent logs."""
    log_file = _get_log_file()
    if not os.path.exists(log_file):
        click.echo("No log file found.")
        return

    if follow:
        try:
            proc = subprocess.Popen(
                ["tail", "-f", "-n", str(lines), log_file],
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            proc.wait()
        except KeyboardInterrupt:
            pass
    else:
        proc = subprocess.run(
            ["tail", "-n", str(lines), log_file],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
