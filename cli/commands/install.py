"""cow install-browser - Install Playwright + Chromium for the browser tool."""

import os
import sys
import subprocess

import click

PLAYWRIGHT_VERSION = "1.52.0"
PLAYWRIGHT_LEGACY_VERSION = "1.28.0"
GLIBC_THRESHOLD = (2, 28)
CHINA_MIRROR = "https://registry.npmmirror.com/-/binary/playwright"


def _has_display() -> bool:
    """Check if a graphical display is available (Linux only)."""
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _is_headless_linux() -> bool:
    return sys.platform == "linux" and not _has_display()


def _get_installed_version() -> str:
    try:
        out = subprocess.check_output(
            [sys.executable, "-c", "import playwright; print(playwright.__version__)"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except Exception:
        return ""


def _version_tuple(v: str):
    try:
        return tuple(int(x) for x in v.split(".")[:3])
    except (ValueError, AttributeError):
        return (0, 0, 0)


def _get_glibc_version():
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


def _is_china_network() -> bool:
    try:
        out = subprocess.check_output(
            [sys.executable, "-m", "pip", "config", "get", "global.index-url"],
            stderr=subprocess.DEVNULL,
        )
        url = out.decode().strip().lower()
        return any(kw in url for kw in ("tsinghua", "aliyun", "npmmirror", "douban", "ustc", "huawei", "tencentyun"))
    except Exception:
        return False


def _pip_install(package_spec: str) -> int:
    """Install a package, retrying with --user on permission failure."""
    python = sys.executable
    ret = subprocess.call([python, "-m", "pip", "install", package_spec])
    if ret != 0:
        click.echo("  Retrying with --user flag...")
        ret = subprocess.call([python, "-m", "pip", "install", "--user", package_spec])
    return ret


@click.command("install-browser")
def install_browser():
    """Install browser tool dependencies (Playwright + Chromium)."""
    python = sys.executable
    legacy_mode = False

    # Determine playwright version based on glibc
    glibc = _get_glibc_version()
    if glibc and glibc < GLIBC_THRESHOLD:
        legacy_mode = True
        glibc_str = f"{glibc[0]}.{glibc[1]}"
        click.echo(click.style(
            f"glibc {glibc_str} detected (< 2.28). "
            f"Will install playwright {PLAYWRIGHT_LEGACY_VERSION} for compatibility.",
            fg="yellow",
        ))
        click.echo(click.style(
            "  Note: upgrade your OS for full browser tool support.",
            fg="yellow",
        ))
        click.echo()

    target_version = PLAYWRIGHT_LEGACY_VERSION if legacy_mode else PLAYWRIGHT_VERSION

    # Step 1: Install playwright package
    click.echo(click.style("[1/3] Installing playwright Python package...", fg="yellow"))
    ret = _pip_install(f"playwright=={target_version}")
    if ret != 0:
        click.echo(click.style("Failed to install playwright package.", fg="red"))
        raise SystemExit(1)

    installed = _get_installed_version()
    if installed:
        click.echo(click.style(f"  playwright {installed} installed.", fg="green"))
    click.echo()

    # Step 2: System dependencies (Linux only)
    if sys.platform == "linux":
        click.echo(click.style("[2/3] Installing system dependencies (Linux)...", fg="yellow"))
        ret = subprocess.call([python, "-m", "playwright", "install-deps", "chromium"])
        if ret != 0:
            click.echo(click.style(
                "  Could not auto-install system deps (may need sudo).\n"
                f"  Run manually: sudo {python} -m playwright install-deps chromium",
                fg="yellow",
            ))
        # Install CJK fonts for proper Chinese/Japanese/Korean rendering in screenshots
        click.echo("  Installing CJK fonts...")
        font_ret = subprocess.call(
            ["sudo", "apt-get", "install", "-y", "fonts-noto-cjk", "fonts-wqy-zenhei"],
            stderr=subprocess.DEVNULL,
        )
        if font_ret != 0:
            click.echo(click.style(
                "  Could not auto-install CJK fonts.\n"
                "  Run manually: sudo apt-get install -y fonts-noto-cjk fonts-wqy-zenhei",
                fg="yellow",
            ))
        else:
            subprocess.call(["fc-cache", "-fv"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            click.echo(click.style("  CJK fonts installed.", fg="green"))
    else:
        click.echo(click.style(f"[2/3] Skipping system deps (not needed on {sys.platform}).", fg="yellow"))
    click.echo()

    # Step 3: Install Chromium
    click.echo(click.style("[3/3] Installing Chromium browser...", fg="yellow"))
    cmd = [python, "-m", "playwright", "install", "chromium"]

    # --only-shell requires playwright >= 1.57
    if _is_headless_linux() and not legacy_mode:
        ver = _version_tuple(installed or "")
        if ver >= (1, 57, 0):
            cmd.append("--only-shell")
            click.echo("  (headless shell for Linux server)")
        else:
            click.echo("  (full Chromium)")
    elif sys.platform == "linux" and _has_display():
        click.echo("  (full browser for Linux desktop)")

    # Use China mirror if pip is configured with a domestic index
    env = os.environ.copy()
    use_mirror = _is_china_network()
    if use_mirror:
        env["PLAYWRIGHT_DOWNLOAD_HOST"] = CHINA_MIRROR
        click.echo(f"  (using China mirror: {CHINA_MIRROR})")

    ret = subprocess.call(cmd, env=env)

    # Fallback: if mirror download failed, retry with official CDN
    if ret != 0 and use_mirror:
        click.echo(click.style(
            "  Mirror download failed, retrying with official CDN...",
            fg="yellow",
        ))
        env_no_mirror = os.environ.copy()
        env_no_mirror.pop("PLAYWRIGHT_DOWNLOAD_HOST", None)
        ret = subprocess.call(cmd, env=env_no_mirror)

    if ret != 0:
        click.echo(click.style("Failed to install Chromium.", fg="red"))
        raise SystemExit(1)

    # Quick smoke test
    click.echo()
    click.echo("Verifying browser installation...")
    ret = subprocess.call(
        [python, "-c", "from playwright.sync_api import sync_playwright; print('OK')"],
        stderr=subprocess.DEVNULL,
    )
    if ret != 0:
        click.echo(click.style(
            "  Warning: playwright import failed. Browser tool may not work on this system.\n"
            "  Consider upgrading your OS or using Docker.",
            fg="yellow",
        ))
    else:
        click.echo(click.style("  Verification passed.", fg="green"))

    click.echo()
    click.echo(click.style("Browser tool ready! Restart CowAgent to enable it.", fg="green"))
