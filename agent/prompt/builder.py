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
    lines = [
        "## 工具系统",
        "",
        "你可以使用以下工具来完成任务。工具名称是大小写敏感的，请严格按照列表中的名称调用。",
        "",
        "### 可用工具",
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
        lines.append("**其他工具**:")
        for name, desc in sorted(tool_map.items()):
            if desc:
                lines.append(f"- `{name}`: {desc}")
            else:
                lines.append(f"- `{name}`")
        lines.append("")
    
    # 工具使用指南
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
        "**完成后**: 工具调用完成后，给用户一个简短、自然的确认或回复，不要直接结束对话。",
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
        "- `MEMORY.md`: 长期记忆，包含重要的背景信息",
        "- `memory/YYYY-MM-DD.md`: 每日记忆，记录当天的对话和事件",
        "",
        "**使用原则**:",
        "- 自然使用记忆，就像你本来就知道",
        "- 不要主动提起或列举记忆，除非用户明确询问",
        "",
    ]
    
    return lines


def _build_user_identity_section(user_identity: Dict[str, str], language: str) -> List[str]:
    """构建用户身份section"""
    if not user_identity:
        return []
    
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
    
    return lines


def _build_docs_section(workspace_dir: str, language: str) -> List[str]:
    """构建文档路径section - 已移除，不再需要"""
    # 不再生成文档section
    return []


def _build_workspace_section(workspace_dir: str, language: str) -> List[str]:
    """构建工作空间section"""
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
        "- ✅ `AGENTS.md`: 已加载 - 工作空间使用指南",
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
    
    lines = [
        "# 项目上下文",
        "",
        "以下项目上下文文件已被加载：",
        "",
    ]
    
    if has_soul:
        lines.append("如果存在 `SOUL.md`，请体现其中定义的人格和语气。避免僵硬、模板化的回复；遵循其指导，除非有更高优先级的指令覆盖它。")
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
        runtime_parts.append(f"模型={runtime_info['model']}")
    if runtime_info.get("workspace"):
        runtime_parts.append(f"工作空间={runtime_info['workspace']}")
    # Only add channel if it's not the default "web"
    if runtime_info.get("channel") and runtime_info.get("channel") != "web":
        runtime_parts.append(f"渠道={runtime_info['channel']}")
    
    if not runtime_parts:
        return []
    
    lines = [
        "## 运行时信息",
        "",
        "运行时: " + " | ".join(runtime_parts),
        ""
    ]
    
    return lines
