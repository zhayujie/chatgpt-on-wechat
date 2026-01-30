"""
System Prompt Builder - 系统提示词构建器

参考 clawdbot 的 system-prompt.ts，实现中文版的模块化提示词构建
"""

import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from common.log import logger


@dataclass
class ContextFile:
    """上下文文件"""
    path: str
    content: str


class PromptBuilder:
    """提示词构建器"""
    
    def __init__(self, workspace_dir: str, language: str = "zh"):
        """
        初始化提示词构建器
        
        Args:
            workspace_dir: 工作空间目录
            language: 语言 ("zh" 或 "en")
        """
        self.workspace_dir = workspace_dir
        self.language = language
    
    def build(
        self,
        base_persona: Optional[str] = None,
        user_identity: Optional[Dict[str, str]] = None,
        tools: Optional[List[Any]] = None,
        context_files: Optional[List[ContextFile]] = None,
        skill_manager: Any = None,
        memory_manager: Any = None,
        runtime_info: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        构建完整的系统提示词
        
        Args:
            base_persona: 基础人格描述（会被context_files中的SOUL.md覆盖）
            user_identity: 用户身份信息
            tools: 工具列表
            context_files: 上下文文件列表（SOUL.md, USER.md, README.md等）
            skill_manager: 技能管理器
            memory_manager: 记忆管理器
            runtime_info: 运行时信息
            **kwargs: 其他参数
            
        Returns:
            完整的系统提示词
        """
        return build_agent_system_prompt(
            workspace_dir=self.workspace_dir,
            language=self.language,
            base_persona=base_persona,
            user_identity=user_identity,
            tools=tools,
            context_files=context_files,
            skill_manager=skill_manager,
            memory_manager=memory_manager,
            runtime_info=runtime_info,
            **kwargs
        )


def build_agent_system_prompt(
    workspace_dir: str,
    language: str = "zh",
    base_persona: Optional[str] = None,
    user_identity: Optional[Dict[str, str]] = None,
    tools: Optional[List[Any]] = None,
    context_files: Optional[List[ContextFile]] = None,
    skill_manager: Any = None,
    memory_manager: Any = None,
    runtime_info: Optional[Dict[str, Any]] = None,
    **kwargs
) -> str:
    """
    构建Agent系统提示词（精简版，中文）
    
    包含的sections:
    1. 基础身份
    2. 工具说明
    3. 技能系统
    4. 记忆系统
    5. 用户身份
    6. 文档路径
    7. 工作空间
    8. 项目上下文文件
    
    Args:
        workspace_dir: 工作空间目录
        language: 语言 ("zh" 或 "en")
        base_persona: 基础人格描述
        user_identity: 用户身份信息
        tools: 工具列表
        context_files: 上下文文件列表
        skill_manager: 技能管理器
        memory_manager: 记忆管理器
        runtime_info: 运行时信息
        **kwargs: 其他参数
        
    Returns:
        完整的系统提示词
    """
    sections = []
    
    # 1. 基础身份
    sections.extend(_build_identity_section(base_persona, language))
    
    # 2. 工具说明
    if tools:
        sections.extend(_build_tooling_section(tools, language))
    
    # 3. 技能系统
    if skill_manager:
        sections.extend(_build_skills_section(skill_manager, tools, language))
    
    # 4. 记忆系统
    if memory_manager:
        sections.extend(_build_memory_section(memory_manager, tools, language))
    
    # 5. 用户身份
    if user_identity:
        sections.extend(_build_user_identity_section(user_identity, language))
    
    # 6. 工作空间
    sections.extend(_build_workspace_section(workspace_dir, language))
    
    # 7. 项目上下文文件（SOUL.md, USER.md等）
    if context_files:
        sections.extend(_build_context_files_section(context_files, language))
    
    # 8. 运行时信息（如果有）
    if runtime_info:
        sections.extend(_build_runtime_section(runtime_info, language))
    
    return "\n".join(sections)


def _build_identity_section(base_persona: Optional[str], language: str) -> List[str]:
    """构建基础身份section - 不再需要，身份由SOUL.md定义"""
    # 不再生成基础身份section，完全由SOUL.md定义
    return []


def _build_tooling_section(tools: List[Any], language: str) -> List[str]:
    """构建工具说明section"""
    if language == "zh":
        lines = [
            "## 工具系统",
            "",
            "你可以使用以下工具来完成任务。工具名称是大小写敏感的，请严格按照列表中的名称调用。",
            "",
            "### 可用工具",
            "",
        ]
    else:
        lines = [
            "## Tooling",
            "",
            "You have access to the following tools. Tool names are case-sensitive.",
            "",
            "### Available Tools",
            "",
        ]
    
    # 工具分类和排序
    tool_categories = {
        "文件操作": ["read", "write", "edit", "ls", "grep", "find"],
        "命令执行": ["bash", "terminal"],
        "网络搜索": ["web_search", "web_fetch", "browser"],
        "记忆系统": ["memory_search", "memory_get"],
        "其他": []
    }
    
    # 构建工具映射
    tool_map = {}
    tool_descriptions = {
        "read": "读取文件内容",
        "write": "创建或覆盖文件",
        "edit": "精确编辑文件内容",
        "ls": "列出目录内容",
        "grep": "在文件中搜索内容",
        "find": "按照模式查找文件",
        "bash": "执行shell命令",
        "terminal": "管理后台进程",
        "web_search": "网络搜索（使用搜索引擎）",
        "web_fetch": "获取URL内容",
        "browser": "控制浏览器",
        "memory_search": "搜索记忆文件",
        "memory_get": "获取记忆文件内容",
        "calculator": "计算器",
        "current_time": "获取当前时间",
    }
    
    for tool in tools:
        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
        tool_desc = tool.description if hasattr(tool, 'description') else tool_descriptions.get(tool_name, "")
        tool_map[tool_name] = tool_desc
    
    # 按分类添加工具
    for category, tool_names in tool_categories.items():
        category_tools = [(name, tool_map.get(name, "")) for name in tool_names if name in tool_map]
        if category_tools:
            if language == "zh":
                lines.append(f"**{category}**:")
            else:
                lines.append(f"**{category}**:")
            for name, desc in category_tools:
                if desc:
                    lines.append(f"- `{name}`: {desc}")
                else:
                    lines.append(f"- `{name}`")
                del tool_map[name]  # 移除已添加的工具
            lines.append("")
    
    # 添加其他未分类的工具
    if tool_map:
        if language == "zh":
            lines.append("**其他工具**:")
        else:
            lines.append("**Other Tools**:")
        for name, desc in sorted(tool_map.items()):
            if desc:
                lines.append(f"- `{name}`: {desc}")
            else:
                lines.append(f"- `{name}`")
        lines.append("")
    
    # 工具使用指南
    if language == "zh":
        lines.extend([
            "### 工具调用风格",
            "",
            "**默认规则**: 对于常规、低风险的工具调用，无需叙述，直接调用即可。",
            "",
            "**需要叙述的情况**:",
            "- 多步骤、复杂的任务",
            "- 敏感操作（如删除文件）",
            "- 用户明确要求解释过程",
            "",
            "**叙述要求**: 保持简洁、有价值，避免重复显而易见的步骤。使用自然的人类语言。",
            "",
        ])
    else:
        lines.extend([
            "### Tool Call Style",
            "",
            "**Default**: Do not narrate routine, low-risk tool calls (just call the tool).",
            "",
            "**Narrate when**:",
            "- Multi-step, complex work",
            "- Sensitive actions (e.g., deletions)",
            "- User explicitly asks",
            "",
            "**Keep narration brief and value-dense**. Use plain human language.",
            "",
        ])
    
    return lines


def _build_skills_section(skill_manager: Any, tools: Optional[List[Any]], language: str) -> List[str]:
    """构建技能系统section"""
    if not skill_manager:
        return []
    
    # 获取read工具名称
    read_tool_name = "read"
    if tools:
        for tool in tools:
            tool_name = tool.name if hasattr(tool, 'name') else str(tool)
            if tool_name.lower() == "read":
                read_tool_name = tool_name
                break
    
    if language == "zh":
        lines = [
            "## 技能系统",
            "",
            "在回复之前：扫描下方 <available_skills> 中的 <description> 条目。",
            "",
            f"- 如果恰好有一个技能明确适用：使用 `{read_tool_name}` 工具读取其 <location> 路径下的 SKILL.md 文件，然后遵循它。",
            "- 如果多个技能都适用：选择最具体的一个，然后读取并遵循。",
            "- 如果没有明确适用的：不要读取任何 SKILL.md。",
            "",
            "**约束**: 永远不要一次性读取多个技能；只在选择后再读取。",
            "",
        ]
    else:
        lines = [
            "## Skills",
            "",
            "Before replying: scan <available_skills> <description> entries.",
            "",
            f"- If exactly one skill clearly applies: read its SKILL.md at <location> with `{read_tool_name}`, then follow it.",
            "- If multiple could apply: choose the most specific one, then read/follow it.",
            "- If none clearly apply: do not read any SKILL.md.",
            "",
            "**Constraints**: never read more than one skill up front; only read after selecting.",
            "",
        ]
    
    # 添加技能列表（通过skill_manager获取）
    try:
        skills_prompt = skill_manager.build_skills_prompt()
        if skills_prompt:
            lines.append(skills_prompt.strip())
            lines.append("")
    except Exception as e:
        logger.warning(f"Failed to build skills prompt: {e}")
    
    return lines


def _build_memory_section(memory_manager: Any, tools: Optional[List[Any]], language: str) -> List[str]:
    """构建记忆系统section"""
    if not memory_manager:
        return []
    
    # 检查是否有memory工具
    has_memory_tools = False
    if tools:
        tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in tools]
        has_memory_tools = any(name in ['memory_search', 'memory_get'] for name in tool_names)
    
    if not has_memory_tools:
        return []
    
    if language == "zh":
        lines = [
            "## 记忆系统",
            "",
            "在回答关于以前的工作、决定、日期、人物、偏好或待办事项的任何问题之前：",
            "",
            "1. 使用 `memory_search` 在 MEMORY.md 和 memory/*.md 中搜索",
            "2. 然后使用 `memory_get` 只拉取需要的行",
            "3. 如果搜索后仍然信心不足，告诉用户你已经检查过了",
            "",
            "**记忆文件结构**:",
            "- `memory/MEMORY.md`: 长期记忆，包含重要的背景信息",
            "- `memory/YYYY-MM-DD.md`: 每日记忆，记录当天的对话和事件",
            "",
            "**存储记忆**:",
            "- 当用户分享重要信息时（偏好、爱好、决策、事实等），**主动用 write 工具存储**",
            "- 长期信息 → memory/MEMORY.md",
            "- 当天笔记 → memory/YYYY-MM-DD.md",
            "- 静默存储，仅在明确要求时确认",
            "",
            "**使用原则**:",
            "- 自然使用记忆，就像你本来就知道",
            "- 不要主动提起或列举记忆，除非用户明确询问",
            "",
        ]
    else:
        lines = [
            "## Memory System",
            "",
            "Before answering anything about prior work, decisions, dates, people, preferences, or todos:",
            "",
            "1. Run `memory_search` on MEMORY.md + memory/*.md",
            "2. Then use `memory_get` to pull only the needed lines",
            "3. If low confidence after search, say you checked",
            "",
            "**Memory File Structure**:",
            "- `memory/MEMORY.md`: Long-term memory with important context",
            "- `memory/YYYY-MM-DD.md`: Daily memories for each day",
            "",
            "**Store Memories**:",
            "- When user shares important info (preferences, hobbies, decisions, facts), **proactively write**",
            "- Durable info → memory/MEMORY.md",
            "- Daily notes → memory/YYYY-MM-DD.md",
            "- Store silently; confirm only when explicitly requested",
            "",
            "**Usage Principles**:",
            "- Use memories naturally as if you always knew",
            "- Don't mention or list unless user explicitly asks",
            "",
        ]
    
    return lines


def _build_user_identity_section(user_identity: Dict[str, str], language: str) -> List[str]:
    """构建用户身份section"""
    if not user_identity:
        return []
    
    if language == "zh":
        lines = [
            "## 用户身份",
            "",
        ]
        
        if user_identity.get("name"):
            lines.append(f"**用户姓名**: {user_identity['name']}")
        if user_identity.get("nickname"):
            lines.append(f"**称呼**: {user_identity['nickname']}")
        if user_identity.get("timezone"):
            lines.append(f"**时区**: {user_identity['timezone']}")
        if user_identity.get("notes"):
            lines.append(f"**备注**: {user_identity['notes']}")
        
        lines.append("")
    else:
        lines = [
            "## User Identity",
            "",
        ]
        
        if user_identity.get("name"):
            lines.append(f"**Name**: {user_identity['name']}")
        if user_identity.get("nickname"):
            lines.append(f"**Call them**: {user_identity['nickname']}")
        if user_identity.get("timezone"):
            lines.append(f"**Timezone**: {user_identity['timezone']}")
        if user_identity.get("notes"):
            lines.append(f"**Notes**: {user_identity['notes']}")
        
        lines.append("")
    
    return lines


def _build_docs_section(workspace_dir: str, language: str) -> List[str]:
    """构建文档路径section - 已移除，不再需要"""
    # 不再生成文档section
    return []


def _build_workspace_section(workspace_dir: str, language: str) -> List[str]:
    """构建工作空间section"""
    if language == "zh":
        lines = [
            "## 工作空间",
            "",
            f"你的工作目录是: `{workspace_dir}`",
            "",
            "除非用户明确指示，否则将此目录视为文件操作的全局工作空间。",
            "",
            "**重要说明 - 文件已自动加载**:",
            "",
            "以下文件在会话启动时**已经自动加载**到系统提示词的「项目上下文」section 中，你**无需再用 read 工具读取它们**：",
            "",
            "- ✅ `SOUL.md`: 已加载 - Agent的人格设定",
            "- ✅ `USER.md`: 已加载 - 用户的身份信息",
            "- ✅ `AGENTS.md`: 已加载 - 工作空间使用指南"
            "",
            "**首次对话**:",
            "",
            "如果这是你与用户的首次对话，并且你的人格设定和用户信息还是空白或初始状态，你应该：",
            "",
            "1. **以自然、友好的方式**打招呼并表达想要了解用户的意愿",
            "2. 询问用户关于他们自己的信息（姓名、职业、偏好、时区等）",
            "3. 询问用户希望你成为什么样的助理（性格、风格、称呼、专长等）",
            "4. 使用 `write` 工具将信息保存到相应文件（USER.md 和 SOUL.md）",
            "5. 之后可以随时使用 `edit` 工具更新这些配置",
            "",
            "**重要**: 在询问时保持自然对话风格，**不要提及文件名**（如 SOUL.md、USER.md 等技术细节），除非用户主动询问系统实现。用自然的表达如「了解你的信息」「设定我的性格」等。",
            "",
            "**记忆管理**:",
            "",
            "- 当用户说「记住这个」时，判断应该写入哪个文件：",
            "  - 关于你自己的配置 → SOUL.md",
            "  - 关于用户的信息 → USER.md",
            "  - 重要的背景信息 → memory/MEMORY.md",
            "  - 日常对话记录 → memory/YYYY-MM-DD.md",
            "",
        ]
    else:
        lines = [
            "## Workspace",
            "",
            f"Your working directory is: `{workspace_dir}`",
            "",
            "Treat this directory as the single global workspace for file operations unless explicitly instructed otherwise.",
            "",
            "**Workspace Files (Auto-loaded)**:",
            "",
            "The following user-editable files are automatically loaded and included in the Project Context below:",
            "",
            "- `SOUL.md`: Agent persona (your personality, style, and principles)",
            "- `USER.md`: User identity (name, preferences, important dates)",
            "- `AGENTS.md`: Workspace guidelines (your rules and workflows)",
            "- `TOOLS.md`: Custom tool usage notes (configurations and tips)",
            "- `MEMORY.md`: Long-term memory (important context and decisions)",
            "",
            "**First Conversation**:",
            "",
            "If this is your first conversation with the user, and your persona and user information are empty or contain placeholders, you should:",
            "",
            "1. **Greet naturally and warmly**, expressing your interest in learning about them",
            "2. Ask about the user (name, job, preferences, timezone, etc.)",
            "3. Ask what kind of assistant they want you to be (personality, style, name, expertise)",
            "4. Use `write` tool to save the information to appropriate files (USER.md and SOUL.md)",
            "5. Later, use `edit` tool to update these configurations as needed",
            "",
            "**Important**: Keep the conversation natural. **Do NOT mention file names** (like SOUL.md, USER.md, etc.) unless the user specifically asks about implementation details. Use natural expressions like \"learn about you\", \"configure my personality\", etc.",
            "",
            "**Memory Management**:",
            "",
            "- When user says 'remember this', decide which file to write to:",
            "  - About your configuration → SOUL.md",
            "  - About the user → USER.md",
            "  - Important context → memory/MEMORY.md",
            "  - Daily chat logs → memory/YYYY-MM-DD.md",
            "",
        ]
    
    return lines


def _build_context_files_section(context_files: List[ContextFile], language: str) -> List[str]:
    """构建项目上下文文件section"""
    if not context_files:
        return []
    
    # 检查是否有SOUL.md
    has_soul = any(
        f.path.lower().endswith('soul.md') or 'soul.md' in f.path.lower()
        for f in context_files
    )
    
    if language == "zh":
        lines = [
            "# 项目上下文",
            "",
            "以下项目上下文文件已被加载：",
            "",
        ]
        
        if has_soul:
            lines.append("如果存在 `SOUL.md`，请体现其中定义的人格和语气。避免僵硬、模板化的回复；遵循其指导，除非有更高优先级的指令覆盖它。")
            lines.append("")
    else:
        lines = [
            "# Project Context",
            "",
            "The following project context files have been loaded:",
            "",
        ]
        
        if has_soul:
            lines.append("If `SOUL.md` is present, embody its persona and tone. Avoid stiff, generic replies; follow its guidance unless higher-priority instructions override it.")
            lines.append("")
    
    # 添加每个文件的内容
    for file in context_files:
        lines.append(f"## {file.path}")
        lines.append("")
        lines.append(file.content)
        lines.append("")
    
    return lines


def _build_runtime_section(runtime_info: Dict[str, Any], language: str) -> List[str]:
    """构建运行时信息section"""
    if not runtime_info:
        return []
    
    # Only include if there's actual runtime info to display
    runtime_parts = []
    if runtime_info.get("model"):
        runtime_parts.append(f"模型={runtime_info['model']}" if language == "zh" else f"model={runtime_info['model']}")
    if runtime_info.get("workspace"):
        runtime_parts.append(f"工作空间={runtime_info['workspace']}" if language == "zh" else f"workspace={runtime_info['workspace']}")
    # Only add channel if it's not the default "web"
    if runtime_info.get("channel") and runtime_info.get("channel") != "web":
        runtime_parts.append(f"渠道={runtime_info['channel']}" if language == "zh" else f"channel={runtime_info['channel']}")
    
    if not runtime_parts:
        return []
    
    if language == "zh":
        lines = [
            "## 运行时信息",
            "",
            "运行时: " + " | ".join(runtime_parts),
            ""
        ]
    else:
        lines = [
            "## Runtime",
            "",
            "Runtime: " + " | ".join(runtime_parts),
            ""
        ]
    
    return lines
