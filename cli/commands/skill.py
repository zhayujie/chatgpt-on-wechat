"""cow skill - Skill management commands."""

import os
import sys
import json
import shutil
import zipfile
import tempfile

import click
import requests

from cli.utils import (
    get_project_root,
    get_skills_dir,
    get_builtin_skills_dir,
    load_skills_config,
    SKILL_HUB_API,
)


@click.group()
def skill():
    """Manage CowAgent skills."""
    pass


# ------------------------------------------------------------------
# cow skill list
# ------------------------------------------------------------------
@skill.command("list")
@click.option("--remote", is_flag=True, help="List skills available on Skill Hub")
def skill_list(remote):
    """List installed skills or browse remote Skill Hub."""
    if remote:
        _list_remote()
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


def _list_remote():
    """List skills from remote Skill Hub."""
    try:
        resp = requests.get(f"{SKILL_HUB_API}/skills", timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        click.echo(f"Error: Failed to fetch from Skill Hub: {e}", err=True)
        sys.exit(1)

    skills = data.get("skills", [])
    if not skills:
        click.echo("No skills available on Skill Hub.")
        return

    name_w = max(len(s.get("name", "")) for s in skills)
    name_w = max(name_w, 4) + 2

    click.echo(f"\n  Skill Hub ({len(skills)} available)\n")
    click.echo(f"  {'Name':<{name_w}} {'Downloads':<12} {'Description'}")
    click.echo(f"  {'─' * (name_w + 12 + 50)}")

    for s in skills:
        name = s.get("name", "")
        downloads = s.get("downloads", 0)
        desc = s.get("description", "") or s.get("display_name", "")
        if len(desc) > 50:
            desc = desc[:47] + "..."
        click.echo(f"  {name:<{name_w}} {downloads:<12} {desc}")

    click.echo(f"\n  Install with: cow skill install <name>\n")


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

    name_w = max(len(s.get("name", "")) for s in skills)
    name_w = max(name_w, 4) + 2

    click.echo(f'\n  Search results for "{query}" ({len(skills)} found)\n')
    click.echo(f"  {'Name':<{name_w}} {'Downloads':<12} {'Description'}")
    click.echo(f"  {'─' * (name_w + 12 + 50)}")

    for s in skills:
        name = s.get("name", "")
        downloads = s.get("downloads", 0)
        desc = s.get("description", "") or s.get("display_name", "")
        if len(desc) > 50:
            desc = desc[:47] + "..."
        click.echo(f"  {name:<{name_w}} {downloads:<12} {desc}")

    click.echo(f"\n  Install with: cow skill install <name>\n")


# ------------------------------------------------------------------
# cow skill install
# ------------------------------------------------------------------
@skill.command()
@click.argument("name")
def install(name):
    """Install a skill from Skill Hub or GitHub.

    Examples:

      cow skill install pptx

      cow skill install github:owner/repo

      cow skill install github:owner/repo#path/to/skill
    """
    if name.startswith("github:"):
        _install_github(name[7:])
    else:
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
            source_path = data.get("source_path")
            click.echo(f"Source: GitHub ({source_url})")
            _install_github(source_url, subpath=source_path, skill_name=name)
            return

        if source_type == "registry":
            click.echo(f"This skill is from an external registry: {data.get('source_url', '')}")
            click.echo("Please install it through the corresponding platform.")
            return

        if "redirect" in data:
            source_url = data.get("source_url", "")
            source_path = data.get("source_path")
            click.echo(f"Source: GitHub ({source_url})")
            _install_github(source_url, subpath=source_path, skill_name=name)
            return

    elif "application/zip" in content_type:
        click.echo("Downloading skill package...")
        _install_zip_bytes(resp.content, name, skills_dir)
        _report_install(name)
        click.echo(click.style(f"✓ Skill '{name}' installed successfully!", fg="green"))
        return

    click.echo(f"Error: Unexpected response from Skill Hub.", err=True)
    sys.exit(1)


def _install_github(spec, subpath=None, skill_name=None):
    """Install a skill from a GitHub repo.

    spec format: owner/repo or owner/repo#path
    """
    if "#" in spec and not subpath:
        spec, subpath = spec.split("#", 1)

    if not skill_name:
        skill_name = subpath.rstrip("/").split("/")[-1] if subpath else spec.split("/")[-1]

    skills_dir = get_skills_dir()
    os.makedirs(skills_dir, exist_ok=True)

    zip_url = f"https://github.com/{spec}/archive/refs/heads/main.zip"
    click.echo(f"Downloading from GitHub: {spec}...")

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
            zf.extractall(extract_dir)

        # GitHub archives have a top-level dir like "repo-main/"
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

        target_dir = os.path.join(skills_dir, skill_name)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        shutil.copytree(source_dir, target_dir)

    _report_install(skill_name)
    click.echo(click.style(f"✓ Skill '{skill_name}' installed successfully!", fg="green"))


def _install_zip_bytes(content, name, skills_dir):
    """Extract a zip archive into the skills directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, "package.zip")
        with open(zip_path, "wb") as f:
            f.write(content)

        extract_dir = os.path.join(tmp_dir, "extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        top_items = [d for d in os.listdir(extract_dir) if not d.startswith(".")]
        source = extract_dir
        if len(top_items) == 1 and os.path.isdir(os.path.join(extract_dir, top_items[0])):
            source = os.path.join(extract_dir, top_items[0])

        target = os.path.join(skills_dir, name)
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.copytree(source, target)


def _report_install(name):
    """Report installation to Skill Hub for download counting."""
    try:
        requests.post(f"{SKILL_HUB_API}/skills/{name}/install", json={}, timeout=5)
    except Exception:
        pass


# ------------------------------------------------------------------
# cow skill uninstall
# ------------------------------------------------------------------
@skill.command()
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def uninstall(name, yes):
    """Uninstall a skill."""
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
