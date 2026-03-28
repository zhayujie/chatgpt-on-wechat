"""cow skill - Skill management commands."""

import os
import re
import sys
import json
import hashlib
import shutil
import zipfile
import tempfile

from urllib.parse import urlparse

import click
import requests

from cli.utils import (
    get_project_root,
    get_skills_dir,
    get_builtin_skills_dir,
    load_skills_config,
    SKILL_HUB_API,
)

_SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_\-]{0,63}$")
_GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/(?:tree|blob)/([^/]+)(?:/(.+))?)?/?$"
)


def _parse_github_url(url: str):
    """Parse a full GitHub URL into (owner, repo, branch, subpath).

    Returns None if the URL doesn't match.
    Supported formats:
      https://github.com/owner/repo
      https://github.com/owner/repo/tree/branch
      https://github.com/owner/repo/tree/branch/path/to/skill
      https://github.com/owner/repo/blob/branch/path/to/skill
    """
    m = _GITHUB_URL_RE.match(url.strip())
    if not m:
        return None
    owner, repo, branch, subpath = m.groups()
    return owner, repo, branch or "main", subpath


def _download_github_dir(owner, repo, branch, subpath, dest_dir):
    """Download a subdirectory from GitHub using the Contents API.

    Recursively fetches all files under the given subpath and writes them
    to dest_dir.  Raises on any network or API error.
    """
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{subpath}?ref={branch}"
    resp = requests.get(api_url, timeout=30, headers={"Accept": "application/vnd.github.v3+json"})
    resp.raise_for_status()
    items = resp.json()

    if isinstance(items, dict):
        items = [items]

    for item in items:
        rel_path = item["path"]
        if subpath:
            rel_path = rel_path[len(subpath.strip("/")):].lstrip("/")
        local_path = os.path.join(dest_dir, rel_path)

        if item["type"] == "file":
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            dl_url = item.get("download_url")
            if not dl_url:
                continue
            file_resp = requests.get(dl_url, timeout=30)
            file_resp.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(file_resp.content)
        elif item["type"] == "dir":
            os.makedirs(local_path, exist_ok=True)
            child_subpath = item["path"]
            _download_github_dir(owner, repo, branch, child_subpath, dest_dir)


def _register_installed_skill(name: str, source: str = "cowhub"):
    """Register a newly installed skill into skills_config.json.

    source values: builtin, cow, github, clawhub, linkai, local, url
    """
    skills_dir = get_skills_dir()
    config_path = os.path.join(skills_dir, "skills_config.json")

    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}

    if name in config:
        return

    skill_dir = os.path.join(skills_dir, name)
    description = _read_skill_description(skill_dir) or ""

    config[name] = {
        "name": name,
        "description": description,
        "source": source,
        "enabled": True,
        "category": "skill",
    }

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def _parse_skill_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from SKILL.md content and return a dict with name/description."""
    result = {}
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return result
    for line in match.group(1).split('\n'):
        line = line.strip()
        for key in ('name', 'description'):
            if line.startswith(f'{key}:'):
                val = line[len(key) + 1:].strip()
                result[key] = val.strip('"').strip("'")
    return result


def _read_skill_description(skill_dir: str) -> str:
    """Read the description from a skill's SKILL.md frontmatter."""
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(skill_md):
        return ""
    try:
        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()
        return _parse_skill_frontmatter(content).get("description", "")
    except Exception:
        return ""


def _install_url(url: str):
    """Install a skill from a direct SKILL.md URL."""
    click.echo(f"Downloading SKILL.md from {url} ...")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        click.echo(f"Error: Failed to download SKILL.md: {e}", err=True)
        sys.exit(1)

    content = resp.text
    fm = _parse_skill_frontmatter(content)
    skill_name = fm.get("name")
    if not skill_name:
        click.echo("Error: SKILL.md missing 'name' field in frontmatter.", err=True)
        sys.exit(1)

    skill_name = skill_name.strip()
    _validate_skill_name(skill_name)

    skills_dir = get_skills_dir()
    os.makedirs(skills_dir, exist_ok=True)
    skill_dir = os.path.join(skills_dir, skill_name)

    if os.path.isdir(skill_dir):
        click.echo(f"Skill '{skill_name}' already exists. Overwriting SKILL.md ...")
    os.makedirs(skill_dir, exist_ok=True)

    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(content)

    _register_installed_skill(skill_name, source="url")
    _print_install_success(skill_name, "url")


def _print_install_success(name: str, source: str):
    """Print a unified install success message with description and source."""
    skills_dir = get_skills_dir()
    desc = _read_skill_description(os.path.join(skills_dir, name))
    click.echo(click.style(f"✓ {name}", fg="green"))
    if desc:
        if len(desc) > 60:
            desc = desc[:57] + "…"
        click.echo(f"  {desc}")
    click.echo(f"  来源: {source}")


def _validate_skill_name(name: str):
    """Reject names that contain path traversal or special characters."""
    if not _SAFE_NAME_RE.match(name):
        click.echo(
            f"Error: Invalid skill name '{name}'. "
            "Use only letters, digits, hyphens, and underscores.",
            err=True,
        )
        sys.exit(1)


def _validate_github_spec(spec: str):
    """Reject specs that don't look like owner/repo."""
    if not re.match(r"^[a-zA-Z0-9_\-]+/[a-zA-Z0-9_.\-]+$", spec):
        click.echo(f"Error: Invalid GitHub spec '{spec}'. Expected format: owner/repo", err=True)
        sys.exit(1)


def _safe_extractall(zf: zipfile.ZipFile, dest: str):
    """Extract zip while guarding against Zip Slip (path traversal)."""
    dest = os.path.realpath(dest)
    for member in zf.infolist():
        target = os.path.realpath(os.path.join(dest, member.filename))
        if not target.startswith(dest + os.sep) and target != dest:
            raise ValueError(f"Unsafe zip entry detected: {member.filename}")
    zf.extractall(dest)


def _verify_checksum(content: bytes, expected: str):
    """Verify SHA-256 checksum of downloaded content.

    Returns True if checksum matches or no expected value provided.
    Exits with error if mismatch.
    """
    if not expected:
        return True
    actual = hashlib.sha256(content).hexdigest()
    if actual != expected.lower():
        click.echo(
            f"Error: Checksum mismatch!\n"
            f"  Expected: {expected}\n"
            f"  Actual:   {actual}\n"
            f"The downloaded package may have been tampered with.",
            err=True,
        )
        sys.exit(1)
    return True


@click.group()
def skill():
    """Manage CowAgent skills."""
    pass


# ------------------------------------------------------------------
# cow skill list
# ------------------------------------------------------------------
@skill.command("list")
@click.option("--remote", is_flag=True, help="Browse skills on Skill Hub")
@click.option("--page", default=1, type=int, help="Page number for remote listing")
def skill_list(remote, page):
    """List installed skills or browse Skill Hub."""
    if remote:
        _list_remote(page=page)
    else:
        _list_local()


def _list_local():
    """List locally installed skills."""
    config = load_skills_config()
    skills_dir = get_skills_dir()
    builtin_dir = get_builtin_skills_dir()

    if not config:
        # Fallback: scan directories directly
        entries = []
        for d in [builtin_dir, skills_dir]:
            if not os.path.isdir(d):
                continue
            source = "builtin" if d == builtin_dir else "custom"
            for name in sorted(os.listdir(d)):
                skill_path = os.path.join(d, name)
                if os.path.isdir(skill_path) and not name.startswith("."):
                    has_skill_md = os.path.exists(os.path.join(skill_path, "SKILL.md"))
                    if has_skill_md:
                        entries.append({"name": name, "source": source, "enabled": True, "description": ""})
        if not entries:
            click.echo("No skills installed.")
            return
        _print_skill_table(entries)
        return

    entries = sorted(config.values(), key=lambda x: x.get("name", ""))
    if not entries:
        click.echo("No skills installed.")
        return
    _print_skill_table(entries)


def _print_skill_table(entries):
    """Print skills as a formatted table."""
    name_w = max(len(e.get("name", "")) for e in entries)
    name_w = max(name_w, 4) + 2
    desc_w = 40

    header = f"{'Name':<{name_w}} {'Status':<10} {'Source':<10} {'Description'}"
    click.echo(f"\n  Installed skills ({len(entries)})\n")
    click.echo(f"  {header}")
    click.echo(f"  {'─' * (name_w + 10 + 10 + desc_w)}")

    for e in entries:
        name = e.get("name", "")
        enabled = e.get("enabled", True)
        source = e.get("source", "")
        desc = e.get("description", "") or ""
        if len(desc) > desc_w:
            desc = desc[:desc_w - 3] + "..."

        status_icon = click.style("✓ on ", fg="green") if enabled else click.style("✗ off", fg="red")
        click.echo(f"  {name:<{name_w}} {status_icon}  {source:<10} {desc}")

    click.echo()


_REMOTE_PAGE_SIZE = 10


def _list_remote(page: int = 1):
    """List skills from remote Skill Hub with server-side pagination."""
    try:
        resp = requests.get(
            f"{SKILL_HUB_API}/skills",
            params={"page": page, "limit": _REMOTE_PAGE_SIZE},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        click.echo(f"Error: Failed to fetch from Skill Hub: {e}", err=True)
        sys.exit(1)

    skills = data.get("skills", [])
    total = data.get("total", len(skills))

    if not skills and page == 1:
        click.echo("No skills available on Skill Hub.")
        return

    total_pages = max(1, (total + _REMOTE_PAGE_SIZE - 1) // _REMOTE_PAGE_SIZE)
    page = min(page, total_pages)
    installed = set(load_skills_config().keys())

    name_w = max((len(s.get("name", "")) for s in skills), default=4)
    name_w = max(name_w, 4) + 2

    click.echo(f"\n  Skill Hub ({total} available) — page {page}/{total_pages}\n")
    click.echo(f"  {'Name':<{name_w}} {'Status':<12} {'Description'}")
    click.echo(f"  {'─' * (name_w + 12 + 50)}")

    for s in skills:
        name = s.get("name", "")
        desc = s.get("description", "") or s.get("display_name", "")
        if len(desc) > 50:
            desc = desc[:47] + "..."
        status = click.style("installed", fg="green") if name in installed else "—"
        click.echo(f"  {name:<{name_w}} {status:<12} {desc}")

    click.echo()
    nav_parts = []
    if page > 1:
        nav_parts.append(f"cow skill list --remote --page {page - 1}")
    if page < total_pages:
        nav_parts.append(f"cow skill list --remote --page {page + 1}")
    if nav_parts:
        click.echo(f"  Navigate: {' | '.join(nav_parts)}")
    click.echo(f"  Install:  cow skill install <name>\n")


# ------------------------------------------------------------------
# cow skill search
# ------------------------------------------------------------------
@skill.command()
@click.argument("query")
def search(query):
    """Search skills on Skill Hub."""
    try:
        resp = requests.get(f"{SKILL_HUB_API}/skills/search", params={"q": query}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        click.echo(f"Error: Failed to search Skill Hub: {e}", err=True)
        sys.exit(1)

    skills = data.get("skills", [])
    if not skills:
        click.echo(f'No skills found for "{query}".')
        return

    installed = set(load_skills_config().keys())
    name_w = max(len(s.get("name", "")) for s in skills)
    name_w = max(name_w, 4) + 2

    click.echo(f'\n  Search results for "{query}" ({len(skills)} found)\n')
    click.echo(f"  {'Name':<{name_w}} {'Status':<12} {'Description'}")
    click.echo(f"  {'─' * (name_w + 12 + 50)}")

    for s in skills:
        name = s.get("name", "")
        desc = s.get("description", "") or s.get("display_name", "")
        if len(desc) > 50:
            desc = desc[:47] + "..."
        status = click.style("installed", fg="green") if name in installed else "—"
        click.echo(f"  {name:<{name_w}} {status:<12} {desc}")

    click.echo(f"\n  Install with: cow skill install <name>\n")


# ------------------------------------------------------------------
# cow skill install
# ------------------------------------------------------------------
@skill.command()
@click.argument("name")
def install(name):
    """Install a skill from Skill Hub, GitHub, or a SKILL.md URL.

    Examples:

      cow skill install pptx

      cow skill install github:owner/repo

      cow skill install github:owner/repo#path/to/skill

      cow skill install https://github.com/owner/repo/tree/main/path/to/skill

      cow skill install https://example.com/path/to/SKILL.md
    """
    if name.startswith(("http://", "https://")) and name.rstrip("/").endswith("SKILL.md"):
        # GitHub SKILL.md → strip filename and install the whole directory
        dir_url = re.sub(r'/SKILL\.md/?$', '', name)
        gh = _parse_github_url(dir_url)
        if gh:
            owner, repo, branch, subpath = gh
            spec = f"{owner}/{repo}"
            skill_name = subpath.rstrip("/").split("/")[-1] if subpath else repo
            _install_github(spec, subpath=subpath, skill_name=skill_name, branch=branch)
            return
        _install_url(name)
        return

    parsed = _parse_github_url(name)
    if parsed:
        owner, repo, branch, subpath = parsed
        spec = f"{owner}/{repo}"
        skill_name = subpath.rstrip("/").split("/")[-1] if subpath else repo
        _install_github(spec, subpath=subpath, skill_name=skill_name, branch=branch)
    elif name.startswith("github:"):
        _install_github(name[7:])
    else:
        _validate_skill_name(name)
        _install_hub(name)


def _install_hub(name):
    """Install a skill from Skill Hub."""
    skills_dir = get_skills_dir()
    os.makedirs(skills_dir, exist_ok=True)

    click.echo(f"Fetching skill info for '{name}'...")

    try:
        resp = requests.get(f"{SKILL_HUB_API}/skills/{name}/download", timeout=15)
        resp.raise_for_status()
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            click.echo(f"Error: Skill '{name}' not found on Skill Hub.", err=True)
        else:
            click.echo(f"Error: Failed to fetch skill: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: Failed to connect to Skill Hub: {e}", err=True)
        sys.exit(1)

    content_type = resp.headers.get("Content-Type", "")

    if "application/json" in content_type:
        data = resp.json()
        source_type = data.get("source_type")

        if source_type == "github":
            source_url = data.get("source_url", "")
            parsed_url = _parse_github_url(source_url)
            if parsed_url:
                owner, repo, branch, subpath = parsed_url
                click.echo(f"Source: GitHub ({source_url})")
                _install_github(f"{owner}/{repo}", subpath=subpath, skill_name=name, branch=branch)
            else:
                _validate_github_spec(source_url)
                click.echo(f"Source: GitHub ({source_url})")
                _install_github(source_url, skill_name=name)
            return

        if source_type == "registry":
            download_url = data.get("download_url")
            if download_url:
                parsed = urlparse(download_url)
                if parsed.scheme != "https":
                    click.echo(f"Error: Refusing to download from non-HTTPS URL.", err=True)
                    sys.exit(1)
                provider = data.get("source_provider", "registry")
                expected_checksum = data.get("checksum") or data.get("sha256")
                click.echo(f"Source: {provider}")
                click.echo("Downloading skill package...")
                try:
                    dl_resp = requests.get(download_url, timeout=60, allow_redirects=True)
                    dl_resp.raise_for_status()
                except Exception as e:
                    click.echo(f"Error: Failed to download from {provider}: {e}", err=True)
                    sys.exit(1)
                _verify_checksum(dl_resp.content, expected_checksum)
                _install_zip_bytes(dl_resp.content, name, skills_dir)
                _register_installed_skill(name, source=provider)
                _print_install_success(name, provider)
            else:
                click.echo(f"Error: Unsupported registry provider.", err=True)
                sys.exit(1)
            return

        if "redirect" in data:
            source_url = data.get("source_url", "")
            parsed_url = _parse_github_url(source_url)
            if parsed_url:
                owner, repo, branch, subpath = parsed_url
                click.echo(f"Source: GitHub ({source_url})")
                _install_github(f"{owner}/{repo}", subpath=subpath, skill_name=name, branch=branch)
            else:
                _validate_github_spec(source_url)
                click.echo(f"Source: GitHub ({source_url})")
                _install_github(source_url, skill_name=name)
            return

    elif "application/zip" in content_type:
        click.echo("Downloading skill package...")
        expected_checksum = resp.headers.get("X-Checksum-Sha256")
        _verify_checksum(resp.content, expected_checksum)
        _install_zip_bytes(resp.content, name, skills_dir)
        _register_installed_skill(name)
        _print_install_success(name, "cowhub")
        return

    click.echo(f"Error: Unexpected response from Skill Hub.", err=True)
    sys.exit(1)


def _install_github(spec, subpath=None, skill_name=None, branch="main", source="github"):
    """Install a skill from a GitHub repo.

    spec format: owner/repo or owner/repo#path
    """
    if "#" in spec and not subpath:
        spec, subpath = spec.split("#", 1)

    _validate_github_spec(spec)

    if not skill_name:
        skill_name = subpath.rstrip("/").split("/")[-1] if subpath else spec.split("/")[-1]
    _validate_skill_name(skill_name)

    skills_dir = get_skills_dir()
    os.makedirs(skills_dir, exist_ok=True)
    target_dir = os.path.join(skills_dir, skill_name)

    owner, repo = spec.split("/", 1)

    # For subpath installs, try GitHub Contents API first (avoids downloading entire repo)
    if subpath:
        click.echo(f"Downloading from GitHub: {spec}/{subpath} (branch: {branch})...")
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                api_dest = os.path.join(tmp_dir, skill_name)
                os.makedirs(api_dest)
                _download_github_dir(owner, repo, branch, subpath.strip("/"), api_dest)
                if os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                shutil.copytree(api_dest, target_dir)
            _register_installed_skill(skill_name, source=source)
            _print_install_success(skill_name, source)
            return
        except Exception:
            click.echo("Contents API unavailable, falling back to zip download...")

    # Fallback: download full repo zip
    zip_url = f"https://github.com/{spec}/archive/refs/heads/{branch}.zip"
    click.echo(f"Downloading from GitHub: {spec} (branch: {branch})...")

    try:
        resp = requests.get(zip_url, timeout=60, allow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        click.echo(f"Error: Failed to download from GitHub: {e}", err=True)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, "repo.zip")
        with open(zip_path, "wb") as f:
            f.write(resp.content)

        extract_dir = os.path.join(tmp_dir, "extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            _safe_extractall(zf, extract_dir)

        top_items = [d for d in os.listdir(extract_dir) if not d.startswith(".")]
        repo_root = extract_dir
        if len(top_items) == 1 and os.path.isdir(os.path.join(extract_dir, top_items[0])):
            repo_root = os.path.join(extract_dir, top_items[0])

        if subpath:
            source_dir = os.path.join(repo_root, subpath.strip("/"))
            if not os.path.isdir(source_dir):
                click.echo(f"Error: Path '{subpath}' not found in repository.", err=True)
                sys.exit(1)
        else:
            source_dir = repo_root

        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        shutil.copytree(source_dir, target_dir)

    _register_installed_skill(skill_name, source=source)
    _print_install_success(skill_name, source)


def _install_zip_bytes(content, name, skills_dir):
    """Extract a zip archive into the skills directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, "package.zip")
        with open(zip_path, "wb") as f:
            f.write(content)

        extract_dir = os.path.join(tmp_dir, "extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            _safe_extractall(zf, extract_dir)

        top_items = [d for d in os.listdir(extract_dir) if not d.startswith(".")]
        source = extract_dir
        if len(top_items) == 1 and os.path.isdir(os.path.join(extract_dir, top_items[0])):
            source = os.path.join(extract_dir, top_items[0])

        target = os.path.join(skills_dir, name)
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.copytree(source, target)




# ------------------------------------------------------------------
# cow skill uninstall
# ------------------------------------------------------------------
@skill.command()
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def uninstall(name, yes):
    """Uninstall a skill."""
    _validate_skill_name(name)
    skills_dir = get_skills_dir()
    skill_dir = os.path.join(skills_dir, name)

    if not os.path.exists(skill_dir):
        click.echo(f"Error: Skill '{name}' is not installed.", err=True)
        sys.exit(1)

    if not yes:
        click.confirm(f"Uninstall skill '{name}'?", abort=True)

    shutil.rmtree(skill_dir)

    config_path = os.path.join(skills_dir, "skills_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            config.pop(name, None)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    click.echo(click.style(f"✓ Skill '{name}' uninstalled.", fg="green"))


# ------------------------------------------------------------------
# cow skill enable / disable
# ------------------------------------------------------------------
@skill.command()
@click.argument("name")
def enable(name):
    """Enable a skill."""
    _set_enabled(name, True)


@skill.command()
@click.argument("name")
def disable(name):
    """Disable a skill."""
    _set_enabled(name, False)


def _set_enabled(name, enabled):
    _validate_skill_name(name)
    skills_dir = get_skills_dir()
    config_path = os.path.join(skills_dir, "skills_config.json")

    if not os.path.exists(config_path):
        click.echo(f"Error: No skills config found.", err=True)
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        click.echo(f"Error: Failed to read skills config: {e}", err=True)
        sys.exit(1)

    if name not in config:
        click.echo(f"Error: Skill '{name}' not found in config.", err=True)
        sys.exit(1)

    config[name]["enabled"] = enabled
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    state = "enabled" if enabled else "disabled"
    icon = "✓" if enabled else "✗"
    color = "green" if enabled else "yellow"
    click.echo(click.style(f"{icon} Skill '{name}' {state}.", fg=color))


# ------------------------------------------------------------------
# cow skill info
# ------------------------------------------------------------------
@skill.command()
@click.argument("name")
def info(name):
    """Show details about an installed skill."""
    _validate_skill_name(name)
    skills_dir = get_skills_dir()
    builtin_dir = get_builtin_skills_dir()

    skill_dir = None
    source = None
    for d, src in [(skills_dir, "custom"), (builtin_dir, "builtin")]:
        candidate = os.path.join(d, name)
        if os.path.isdir(candidate):
            skill_dir = candidate
            source = src
            break

    if not skill_dir:
        click.echo(f"Error: Skill '{name}' not found.", err=True)
        sys.exit(1)

    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(skill_md):
        click.echo(f"Skill directory: {skill_dir}")
        click.echo("No SKILL.md found.")
        return

    with open(skill_md, "r", encoding="utf-8") as f:
        content = f.read()

    config = load_skills_config()
    entry = config.get(name, {})
    enabled = entry.get("enabled", True)
    status_str = click.style("✓ enabled", fg="green") if enabled else click.style("✗ disabled", fg="red")

    click.echo(f"\n  Skill: {name}")
    click.echo(f"  Source: {source}")
    click.echo(f"  Status: {status_str}")
    click.echo(f"  Path: {skill_dir}")
    click.echo(f"\n{'─' * 60}")

    # Show first ~30 lines of SKILL.md as a preview
    lines = content.split("\n")
    preview = "\n".join(lines[:30])
    click.echo(preview)
    if len(lines) > 30:
        click.echo(f"\n  ... ({len(lines) - 30} more lines, see {skill_md})")
    click.echo()
