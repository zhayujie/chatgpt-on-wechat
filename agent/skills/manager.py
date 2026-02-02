"""
Skill manager for managing skill lifecycle and operations.
"""

import os
from typing import Dict, List, Optional
from pathlib import Path
from common.log import logger
from agent.skills.types import Skill, SkillEntry, SkillSnapshot
from agent.skills.loader import SkillLoader
from agent.skills.formatter import format_skill_entries_for_prompt


class SkillManager:
    """Manages skills for an agent."""
    
    def __init__(
        self,
        workspace_dir: Optional[str] = None,
        managed_skills_dir: Optional[str] = None,
        extra_dirs: Optional[List[str]] = None,
        config: Optional[Dict] = None,
    ):
        """
        Initialize the skill manager.
        
        :param workspace_dir: Agent workspace directory
        :param managed_skills_dir: Managed skills directory (e.g., ~/.cow/skills)
        :param extra_dirs: Additional skill directories
        :param config: Configuration dictionary
        """
        self.workspace_dir = workspace_dir
        self.managed_skills_dir = managed_skills_dir or self._get_default_managed_dir()
        self.extra_dirs = extra_dirs or []
        self.config = config or {}
        
        self.loader = SkillLoader(workspace_dir=workspace_dir)
        self.skills: Dict[str, SkillEntry] = {}
        
        # Load skills on initialization
        self.refresh_skills()
    
    def _get_default_managed_dir(self) -> str:
        """Get the default managed skills directory."""
        # Use project root skills directory as default
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(project_root, 'skills')
    
    def refresh_skills(self):
        """Reload all skills from configured directories."""
        workspace_skills_dir = None
        if self.workspace_dir:
            workspace_skills_dir = os.path.join(self.workspace_dir, 'skills')
        
        self.skills = self.loader.load_all_skills(
            managed_dir=self.managed_skills_dir,
            workspace_skills_dir=workspace_skills_dir,
            extra_dirs=self.extra_dirs,
        )
        
        logger.debug(f"SkillManager: Loaded {len(self.skills)} skills")
    
    def get_skill(self, name: str) -> Optional[SkillEntry]:
        """
        Get a skill by name.
        
        :param name: Skill name
        :return: SkillEntry or None if not found
        """
        return self.skills.get(name)
    
    def list_skills(self) -> List[SkillEntry]:
        """
        Get all loaded skills.
        
        :return: List of all skill entries
        """
        return list(self.skills.values())
    
    def filter_skills(
        self,
        skill_filter: Optional[List[str]] = None,
        include_disabled: bool = False,
    ) -> List[SkillEntry]:
        """
        Filter skills based on criteria.
        
        Simple rule: Skills are auto-enabled if requirements are met.
        - Has required API keys → included
        - Missing API keys → excluded
        
        :param skill_filter: List of skill names to include (None = all)
        :param include_disabled: Whether to include skills with disable_model_invocation=True
        :return: Filtered list of skill entries
        """
        from agent.skills.config import should_include_skill
        
        entries = list(self.skills.values())
        
        # Check requirements (platform, binaries, env vars)
        entries = [e for e in entries if should_include_skill(e, self.config)]
        
        # Apply skill filter
        if skill_filter is not None:
            # Flatten and normalize skill names (handle both strings and nested lists)
            normalized = []
            for item in skill_filter:
                if isinstance(item, str):
                    name = item.strip()
                    if name:
                        normalized.append(name)
                elif isinstance(item, list):
                    # Handle nested lists
                    for subitem in item:
                        if isinstance(subitem, str):
                            name = subitem.strip()
                            if name:
                                normalized.append(name)
            
            if normalized:
                entries = [e for e in entries if e.skill.name in normalized]
        
        # Filter out disabled skills unless explicitly requested
        if not include_disabled:
            entries = [e for e in entries if not e.skill.disable_model_invocation]
        
        return entries
    
    def build_skills_prompt(
        self,
        skill_filter: Optional[List[str]] = None,
    ) -> str:
        """
        Build a formatted prompt containing available skills.
        
        :param skill_filter: Optional list of skill names to include
        :return: Formatted skills prompt
        """
        from common.log import logger
        entries = self.filter_skills(skill_filter=skill_filter, include_disabled=False)
        logger.debug(f"[SkillManager] Filtered {len(entries)} skills for prompt (total: {len(self.skills)})")
        if entries:
            skill_names = [e.skill.name for e in entries]
            logger.debug(f"[SkillManager] Skills to include: {skill_names}")
        result = format_skill_entries_for_prompt(entries)
        logger.debug(f"[SkillManager] Generated prompt length: {len(result)}")
        return result
    
    def build_skill_snapshot(
        self,
        skill_filter: Optional[List[str]] = None,
        version: Optional[int] = None,
    ) -> SkillSnapshot:
        """
        Build a snapshot of skills for a specific run.
        
        :param skill_filter: Optional list of skill names to include
        :param version: Optional version number for the snapshot
        :return: SkillSnapshot
        """
        entries = self.filter_skills(skill_filter=skill_filter, include_disabled=False)
        prompt = format_skill_entries_for_prompt(entries)
        
        skills_info = []
        resolved_skills = []
        
        for entry in entries:
            skills_info.append({
                'name': entry.skill.name,
                'primary_env': entry.metadata.primary_env if entry.metadata else None,
            })
            resolved_skills.append(entry.skill)
        
        return SkillSnapshot(
            prompt=prompt,
            skills=skills_info,
            resolved_skills=resolved_skills,
            version=version,
        )
    
    def sync_skills_to_workspace(self, target_workspace_dir: str):
        """
        Sync all loaded skills to a target workspace directory.
        
        This is useful for sandbox environments where skills need to be copied.
        
        :param target_workspace_dir: Target workspace directory
        """
        import shutil
        
        target_skills_dir = os.path.join(target_workspace_dir, 'skills')
        
        # Remove existing skills directory
        if os.path.exists(target_skills_dir):
            shutil.rmtree(target_skills_dir)
        
        # Create new skills directory
        os.makedirs(target_skills_dir, exist_ok=True)
        
        # Copy each skill
        for entry in self.skills.values():
            skill_name = entry.skill.name
            source_dir = entry.skill.base_dir
            target_dir = os.path.join(target_skills_dir, skill_name)
            
            try:
                shutil.copytree(source_dir, target_dir)
                logger.debug(f"Synced skill '{skill_name}' to {target_dir}")
            except Exception as e:
                logger.warning(f"Failed to sync skill '{skill_name}': {e}")
        
        logger.info(f"Synced {len(self.skills)} skills to {target_skills_dir}")
    
    def get_skill_by_key(self, skill_key: str) -> Optional[SkillEntry]:
        """
        Get a skill by its skill key (which may differ from name).
        
        :param skill_key: Skill key to look up
        :return: SkillEntry or None
        """
        for entry in self.skills.values():
            if entry.metadata and entry.metadata.skill_key == skill_key:
                return entry
            if entry.skill.name == skill_key:
                return entry
        return None
