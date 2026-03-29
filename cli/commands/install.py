"""cow install-browser - Install Playwright + Chromium for the browser tool."""

import os
import sys
import subprocess

import click

MIN_PLAYWRIGHT_VERSION = "1.49.0"


def _has_display() -> bool:
    """Check if a graphical display is available (Linux only)."""
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _is_headless_linux() -> bool:
    """True when running on a Linux server without a display."""
    return sys.platform == "linux" and not _has_display()


def _get_installed_version() -> str:
    """Return installed playwright version string, or empty if not installed."""
    python = sys.executable
    try:
        out = subprocess.check_output(
            [python, "-c", "import playwright; print(playwright.__version__)"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except Exception:
        return ""


def _version_tuple(v: str):
    """Parse '1.49.0' into (1, 49, 0)."""
    try:
        return tuple(int(x) for x in v.split(".")[:3])
    except (ValueError, AttributeError):
        return (0, 0, 0)


@click.command("install-browser")
def install_browser():
    """Install browser tool dependencies (Playwright + Chromium)."""
    python = sys.executable

    # Step 1: Install / upgrade playwright package
    click.echo(click.style("[1/3] Installing playwright Python package...", fg="yellow"))
    ret = subprocess.call([python, "-m", "pip", "install", f"playwright>={MIN_PLAYWRIGHT_VERSION}"])
    if ret != 0:
        click.echo(click.style("Failed to install playwright package.", fg="red"))
        raise SystemExit(1)

    installed = _get_installed_version()
    if installed:
        click.echo(click.style(f"playwright {installed} installed.", fg="green"))
    else:
        click.echo(click.style("playwright package installed.", fg="green"))
    click.echo()

    # Step 2: System dependencies (Linux only)
    if sys.platform == "linux":
        click.echo(click.style("[2/3] Installing system dependencies (Linux)...", fg="yellow"))
        ret = subprocess.call([python, "-m", "playwright", "install-deps", "chromium"])
        if ret != 0:
            click.echo(click.style(
                "Could not auto-install system deps (may need sudo).\n"
                f"  Run manually: sudo {python} -m playwright install-deps chromium",
                fg="yellow",
            ))
    else:
        click.echo(click.style(f"[2/3] Skipping system deps (not needed on {sys.platform}).", fg="yellow"))
    click.echo()

    # Step 3: Install Chromium
    click.echo(click.style("[3/3] Installing Chromium browser...", fg="yellow"))
    cmd = [python, "-m", "playwright", "install", "chromium"]

    # --only-shell requires playwright >= 1.57
    if _is_headless_linux():
        ver = _version_tuple(_get_installed_version())
        if ver >= (1, 57, 0):
            cmd.append("--only-shell")
            click.echo("  (headless shell for Linux server)")
        else:
            click.echo("  (full Chromium - upgrade to playwright>=1.57 for headless-only shell)")
    elif sys.platform == "linux":
        click.echo("  (full browser for Linux desktop)")

    ret = subprocess.call(cmd)
    if ret != 0:
        click.echo(click.style("Failed to install Chromium.", fg="red"))
        raise SystemExit(1)

    click.echo()
    click.echo(click.style("Browser tool ready! Restart CowAgent to enable it.", fg="green"))
