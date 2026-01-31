"""
Configuration support for skills.
"""

import os
import platform
from typing import Dict, Optional, List
from agent.skills.types import SkillEntry


def resolve_runtime_platform() -> str:
    """Get the current runtime platform."""
    return platform.system().lower()


def has_binary(bin_name: str) -> bool:
    """
    Check if a binary is available in PATH.
    
    :param bin_name: Binary name to check
    :return: True if binary is available
    """
    import shutil
    return shutil.which(bin_name) is not None


def has_any_binary(bin_names: List[str]) -> bool:
    """
    Check if any of the given binaries is available.
    
    :param bin_names: List of binary names to check
    :return: True if at least one binary is available
    """
    return any(has_binary(bin_name) for bin_name in bin_names)


def has_env_var(env_name: str) -> bool:
    """
    Check if an environment variable is set.
    
    :param env_name: Environment variable name
    :return: True if environment variable is set
    """
    return env_name in os.environ and bool(os.environ[env_name].strip())


def get_skill_config(config: Optional[Dict], skill_name: str) -> Optional[Dict]:
    """
    Get skill-specific configuration.
    
    :param config: Global configuration dictionary
    :param skill_name: Name of the skill
    :return: Skill configuration or None
    """
    if not config:
        return None
    
    skills_config = config.get('skills', {})
    if not isinstance(skills_config, dict):
        return None
    
    entries = skills_config.get('entries', {})
    if not isinstance(entries, dict):
        return None
    
    return entries.get(skill_name)


def should_include_skill(
    entry: SkillEntry,
    config: Optional[Dict] = None,
    current_platform: Optional[str] = None,
    lenient: bool = True,
) -> bool:
    """
    Determine if a skill should be included based on requirements.
    
    Similar to clawdbot's shouldIncludeSkill logic, but with lenient mode:
    - In lenient mode (default): Only check explicit disable and platform, ignore missing requirements
    - In strict mode: Check all requirements (binary, env vars, config)
    
    :param entry: SkillEntry to check
    :param config: Configuration dictionary
    :param current_platform: Current platform (default: auto-detect)
    :param lenient: If True, ignore missing requirements and load all skills (default: True)
    :return: True if skill should be included
    """
    metadata = entry.metadata
    skill_name = entry.skill.name
    skill_config = get_skill_config(config, skill_name)
    
    # Always check if skill is explicitly disabled in config
    if skill_config and skill_config.get('enabled') is False:
        return False
    
    if not metadata:
        return True
    
    # Always check platform requirements (can't work on wrong platform)
    if metadata.os:
        platform_name = current_platform or resolve_runtime_platform()
        # Map common platform names
        platform_map = {
            'darwin': 'darwin',
            'linux': 'linux',
            'windows': 'win32',
        }
        normalized_platform = platform_map.get(platform_name, platform_name)
        
        if normalized_platform not in metadata.os:
            return False
    
    # If skill has 'always: true', include it regardless of other requirements
    if metadata.always:
        return True
    
    # In lenient mode, skip requirement checks and load all skills
    # Skills will fail gracefully at runtime if requirements are missing
    if lenient:
        return True
    
    # Strict mode: Check all requirements
    if metadata.requires:
        # Check required binaries (all must be present)
        required_bins = metadata.requires.get('bins', [])
        if required_bins:
            if not all(has_binary(bin_name) for bin_name in required_bins):
                return False
        
        # Check anyBins (at least one must be present)
        any_bins = metadata.requires.get('anyBins', [])
        if any_bins:
            if not has_any_binary(any_bins):
                return False
        
        # Check environment variables (with config fallback)
        required_env = metadata.requires.get('env', [])
        if required_env:
            for env_name in required_env:
                # Check in order: 1) env var, 2) skill config env, 3) skill config apiKey (if primaryEnv)
                if has_env_var(env_name):
                    continue
                if skill_config:
                    # Check skill config env dict
                    skill_env = skill_config.get('env', {})
                    if isinstance(skill_env, dict) and env_name in skill_env:
                        continue
                    # Check skill config apiKey (if this is the primaryEnv)
                    if metadata.primary_env == env_name and skill_config.get('apiKey'):
                        continue
                # Requirement not satisfied
                return False
        
        # Check config paths
        required_config = metadata.requires.get('config', [])
        if required_config and config:
            for config_path in required_config:
                if not is_config_path_truthy(config, config_path):
                    return False
    
    return True


def is_config_path_truthy(config: Dict, path: str) -> bool:
    """
    Check if a config path resolves to a truthy value.
    
    :param config: Configuration dictionary
    :param path: Dot-separated path (e.g., 'skills.enabled')
    :return: True if path resolves to truthy value
    """
    parts = path.split('.')
    current = config
    
    for part in parts:
        if not isinstance(current, dict):
            return False
        current = current.get(part)
        if current is None:
            return False
    
    # Check if value is truthy
    if isinstance(current, bool):
        return current
    if isinstance(current, (int, float)):
        return current != 0
    if isinstance(current, str):
        return bool(current.strip())
    
    return bool(current)


def resolve_config_path(config: Dict, path: str):
    """
    Resolve a dot-separated config path to its value.
    
    :param config: Configuration dictionary
    :param path: Dot-separated path
    :return: Value at path or None
    """
    parts = path.split('.')
    current = config
    
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
        if current is None:
            return None
    
    return current
