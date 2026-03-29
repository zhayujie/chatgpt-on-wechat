"""cow install-browser - Install Playwright + Chromium for the browser tool."""

import os
import sys
import subprocess

import click

MIN_PLAYWRIGHT_VERSION = "1.49.0"
MIN_GLIBC_VERSION = (2, 28)


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


def _get_glibc_version():
    """Return glibc version as (major, minor) tuple, or None if unavailable."""
    if sys.platform != "linux":
        return None
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6")
        gnu_get_libc_version = libc.gnu_get_libc_version
        gnu_get_libc_version.restype = ctypes.c_char_p
        ver = gnu_get_libc_version().decode()
        parts = ver.split(".")
        return (int(parts[0]), int(parts[1]))
    except Exception:
        return None


@click.command("install-browser")
def install_browser():
    """Install browser tool dependencies (Playwright + Chromium)."""
    python = sys.executable

    # Pre-check: glibc version on Linux
    if sys.platform == "linux":
        glibc = _get_glibc_version()
        if glibc and glibc < MIN_GLIBC_VERSION:
            glibc_str = f"{glibc[0]}.{glibc[1]}"
            click.echo(click.style(
                f"Your system glibc version is {glibc_str}, "
                f"but Playwright requires glibc >= {MIN_GLIBC_VERSION[0]}.{MIN_GLIBC_VERSION[1]}.\n"
                f"(e.g. Ubuntu 18.04 ships glibc 2.27, CentOS 7 ships glibc 2.17)\n\n"
                f"Options:\n"
                f"  1. Upgrade your OS (e.g. Ubuntu 20.04+, Debian 10+, CentOS 8+)\n"
                f"  2. Use Docker with a newer Linux image\n"
                f"  3. Install an older playwright version manually (not recommended):\n"
                f"     pip install playwright==1.30.0 && playwright install chromium",
                fg="red",
            ))
            raise SystemExit(1)

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
            click.echo("  (full Chromium - upgrade to playwright>=1.57 for smaller headless-only install)")
    elif sys.platform == "linux":
        click.echo("  (full browser for Linux desktop)")

    ret = subprocess.call(cmd)
    if ret != 0:
        click.echo(click.style("Failed to install Chromium.", fg="red"))
        raise SystemExit(1)

    click.echo()
    click.echo(click.style("Browser tool ready! Restart CowAgent to enable it.", fg="green"))
