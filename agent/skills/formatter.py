"""
Skill formatter for generating prompts from skills.
"""

from typing import List
from agent.skills.types import Skill, SkillEntry


def format_skills_for_prompt(skills: List[Skill]) -> str:
    """
    Format skills for inclusion in a system prompt.
    
    Uses XML format per Agent Skills standard.
    Skills with disable_model_invocation=True are excluded.
    
    :param skills: List of skills to format
    :return: Formatted prompt text
    """
    # Filter out skills that should not be invoked by the model
    visible_skills = [s for s in skills if not s.disable_model_invocation]
    
    if not visible_skills:
        return ""
    
    lines = [
        "",
        "<available_skills>",
    ]

    for skill in visible_skills:
        lines.append("  <skill>")
        lines.append(f"    <name>{_escape_xml(skill.name)}</name>")
        lines.append(f"    <description>{_escape_xml(skill.description)}</description>")
        lines.append(f"    <location>{_escape_xml(skill.file_path)}</location>")
        lines.append("  </skill>")
    
    lines.append("</available_skills>")
    
    return "\n".join(lines)


def format_skill_entries_for_prompt(entries: List[SkillEntry]) -> str:
    """
    Format skill entries for inclusion in a system prompt.
    
    :param entries: List of skill entries to format
    :return: Formatted prompt text
    """
    skills = [entry.skill for entry in entries]
    return format_skills_for_prompt(skills)


def _escape_xml(text: str) -> str:
    """Escape XML special characters."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))
