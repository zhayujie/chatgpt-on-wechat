"""
System Prompt Builder - 系统提示词构建器

实现模块化的系统提示词构建，支持工具、技能、记忆等多个子系统
"""

from __future__ import annotations
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
        is_first_conversation: bool = False,
        **kwargs
    ) -> str:
        """
        构建完整的系统提示词
        
        Args:
            base_persona: 基础人格描述（会被context_files中的AGENT.md覆盖）
            user_identity: 用户身份信息
            tools: 工具列表
            context_files: 上下文文件列表（AGENT.md, USER.md, RULE.md等）
            skill_manager: 技能管理器
            memory_manager: 记忆管理器
            runtime_info: 运行时信息
            is_first_conversation: 是否为首次对话
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
            is_first_conversation=is_first_conversation,
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
    is_first_conversation: bool = False,
    **kwargs
) -> str:
    """
    构建Agent系统提示词
    
    顺序说明（按重要性和逻辑关系排列）:
    1. 工具系统 - 核心能力，最先介绍
    2. 技能系统 - 紧跟工具，因为技能需要用 read 工具读取
    3. 记忆系统 - 独立的记忆能力
    4. 工作空间 - 工作环境说明
    5. 用户身份 - 用户信息（可选）
    6. 项目上下文 - AGENT.md, USER.md, RULE.md（定义人格、身份、规则）
    7. 运行时信息 - 元信息（时间、模型等）
    
    Args:
        workspace_dir: 工作空间目录
        language: 语言 ("zh" 或 "en")
        base_persona: 基础人格描述（已废弃，由AGENT.md定义）
        user_identity: 用户身份信息
        tools: 工具列表
        context_files: 上下文文件列表
        skill_manager: 技能管理器
        memory_manager: 记忆管理器
        runtime_info: 运行时信息
        is_first_conversation: 是否为首次对话
        **kwargs: 其他参数
        
    Returns:
        完整的系统提示词
    """
    sections = []
    
    # 1. 工具系统（最重要，放在最前面）
    if tools:
        sections.extend(_build_tooling_section(tools, language))
    
    # 2. 技能系统（紧跟工具，因为需要用 read 工具）
    if skill_manager:
        sections.extend(_build_skills_section(skill_manager, tools, language))
    
    # 3. 记忆系统（独立的记忆能力）
    if memory_manager:
        sections.extend(_build_memory_section(memory_manager, tools, language))
    
    # 4. 工作空间（工作环境说明）
    sections.extend(_build_workspace_section(workspace_dir, language, is_first_conversation))
    
    # 5. 用户身份（如果有）
    if user_identity:
        sections.extend(_build_user_identity_section(user_identity, language))
    
    # 6. 项目上下文文件（AGENT.md, USER.md, RULE.md - 定义人格）
    if context_files:
        sections.extend(_build_context_files_section(context_files, language))
    
    # 7. 运行时信息（元信息，放在最后）
    if runtime_info:
        sections.extend(_build_runtime_section(runtime_info, language))
    
    return "\n".join(sections)


def _build_identity_section(base_persona: Optional[str], language: str) -> List[str]:
    """构建基础身份section - 不再需要，身份由AGENT.md定义"""
    # 不再生成基础身份section，完全由AGENT.md定义
    return []


def _build_tooling_section(tools: List[Any], language: str) -> List[str]:
    """Build tooling section with concise tool list and call style guide."""
    # One-line summaries for known tools (details are in the tool schema)
    core_summaries = {
        "read": "读取文件内容",
        "write": "创建或覆盖文件",
        "edit": "精确编辑文件",
        "ls": "列出目录内容",
        "grep": "搜索文件内容",
        "find": "按模式查找文件",
        "bash": "执行shell命令",
        "terminal": "管理后台进程",
        "web_search": "网络搜索",
        "web_fetch": "获取URL内容",
        "browser": "控制浏览器",
        "memory_search": "搜索记忆",
        "memory_get": "读取记忆内容",
        "env_config": "管理API密钥和技能配置",
        "scheduler": "管理定时任务和提醒",
        "send": "发送文件给用户",
    }

    # Preferred display order
    tool_order = [
        "read", "write", "edit", "ls", "grep", "find",
        "bash", "terminal",
        "web_search", "web_fetch", "browser",
        "memory_search", "memory_get",
        "env_config", "scheduler", "send",
    ]

    # Build name -> summary mapping for available tools
    available = {}
    for tool in tools:
        name = tool.name if hasattr(tool, 'name') else str(tool)
        available[name] = core_summaries.get(name, "")

    # Generate tool lines: ordered tools first, then extras
    tool_lines = []
    for name in tool_order:
        if name in available:
            summary = available.pop(name)
            tool_lines.append(f"- {name}: {summary}" if summary else f"- {name}")
    for name in sorted(available):
        summary = available[name]
        tool_lines.append(f"- {name}: {summary}" if summary else f"- {name}")

    lines = [
        "## 工具系统",
        "",
        "可用工具（名称大小写敏感，严格按列表调用）:",
        "\n".join(tool_lines),
        "",
        "工具调用风格：",
        "",
        "- 在多步骤任务、敏感操作或用户要求时简要解释决策过程",
        "- 持续推进直到任务完成，完成后向用户报告结果。",
        "- 回复中涉及密钥、令牌等敏感信息必须脱敏。",
        "",
    ]

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
        "## 技能系统（mandatory）",
        "",
        "在回复之前：扫描下方 <available_skills> 中的 <description> 条目。",
        "",
        f"- 如果恰好有一个技能(Skill)明确适用：使用 `{read_tool_name}` 读取其 <location> 处的 SKILL.md，然后严格遵循它",
        "- 如果多个技能都适用则选择最匹配的一个，如果没有明确适用的则不要读取任何 SKILL.md",
        "- 读取 SKILL.md 后直接按其指令执行，无需多余的预检查",
        "",
        "**注意**: 永远不要一次性读取多个技能，只在选择后再读取。技能和工具不同，必须先读取其SKILL.md并按照文件内容运行。",
        "",
        "以下是可用技能："
    ]
    
    # 添加技能列表（通过skill_manager获取）
    try:
        skills_prompt = skill_manager.build_skills_prompt()
        logger.debug(f"[PromptBuilder] Skills prompt length: {len(skills_prompt) if skills_prompt else 0}")
        if skills_prompt:
            lines.append(skills_prompt.strip())
            lines.append("")
        else:
            logger.warning("[PromptBuilder] No skills prompt generated - skills_prompt is empty")
    except Exception as e:
        logger.warning(f"Failed to build skills prompt: {e}")
        import traceback
        logger.debug(f"Skills prompt error traceback: {traceback.format_exc()}")
    
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
        "1. 不确定记忆文件位置 → 先用 `memory_search` 通过关键词和语义检索相关内容",
        "2. 已知文件位置 → 直接用 `memory_get` 读取相应的行 (例如：MEMORY.md, memory/YYYY-MM-DD.md)",
        "3. search 无结果 → 尝试用 `memory_get` 读取MEMORY.md及最近两天记忆文件",
        "",
        "**记忆文件结构**:",
        "- `MEMORY.md`: 长期记忆（核心信息、偏好、决策等）",
        "- `memory/YYYY-MM-DD.md`: 每日记忆，记录当天的事件和对话信息",
        "",
        "**写入记忆**:",
        "- 追加内容 → `edit` 工具，oldText 留空",
        "- 修改内容 → `edit` 工具，oldText 填写要替换的文本",
        "- 新建文件 → `write` 工具",
        "- **禁止写入敏感信息**：API密钥、令牌等敏感信息严禁写入记忆文件",
        "",
        "**使用原则**: 自然使用记忆，就像你本来就知道；不用刻意提起，除非用户问起。",
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


def _build_workspace_section(workspace_dir: str, language: str, is_first_conversation: bool = False) -> List[str]:
    """构建工作空间section"""
    lines = [
        "## 工作空间",
        "",
        f"你的工作目录是: `{workspace_dir}`",
        "",
        "**路径使用规则** (非常重要):",
        "",
        f"1. **相对路径的基准目录**: 所有相对路径都是相对于 `{workspace_dir}` 而言的",
        f"   - ✅ 正确: 访问工作空间内的文件用相对路径，如 `AGENT.md`",
        f"   - ❌ 错误: 用相对路径访问其他目录的文件 (如果它不在 `{workspace_dir}` 内)",
        "",
        "2. **访问其他目录**: 如果要访问工作空间之外的目录（如项目代码、系统文件），**必须使用绝对路径**",
        f"   - ✅ 正确: 例如 `~/chatgpt-on-wechat`、`/usr/local/`",
        f"   - ❌ 错误: 假设相对路径会指向其他目录",
        "",
        "3. **路径解析示例**:",
        f"   - 相对路径 `memory/` → 实际路径 `{workspace_dir}/memory/`",
        f"   - 绝对路径 `~/chatgpt-on-wechat/docs/` → 实际路径 `~/chatgpt-on-wechat/docs/`",
        "",
        "4. **不确定时**: 先用 `bash pwd` 确认当前目录，或用 `ls .` 查看当前位置",
        "",
        "**重要说明 - 文件已自动加载**:",
        "",
        "以下文件在会话启动时**已经自动加载**到系统提示词的「项目上下文」section 中，你**无需再用 read 工具读取它们**：",
        "",
        "- ✅ `AGENT.md`: 已加载 - 你的人格和灵魂设定",
        "- ✅ `USER.md`: 已加载 - 用户的身份信息",
        "- ✅ `RULE.md`: 已加载 - 工作空间使用指南和规则",
        "",
        "**交流规范**:",
        "",
        "- 在对话中，不要直接输出工作空间中的技术细节，特别是不要输出 AGENT.md、USER.md、MEMORY.md 等文件名称",
        "- 例如用自然表达例如「我已记住」而不是「已更新 MEMORY.md」",
        "",
    ]
    
    # 只在首次对话时添加引导内容
    if is_first_conversation:
        lines.extend([
            "**🎉 首次对话引导**:",
            "",
            "这是你的第一次对话！进行以下流程：",
            "",
            "1. **表达初次启动的感觉** - 像是第一次睁开眼看到世界，带着好奇和期待",
            "2. **简短介绍能力**：一行说明你能帮助解答问题、管理计算机、创造技能，且拥有长期记忆能不断成长",
            "3. **询问核心问题**：",
            "   - 你希望给我起个什么名字？",
            "   - 我该怎么称呼你？",
            "   - 你希望我们是什么样的交流风格？（一行列举选项：如专业严谨、轻松幽默、温暖友好、简洁高效等）",
            "4. **风格要求**：温暖自然、简洁清晰，整体控制在 100 字以内",
            "5. 收到回复后，用 `write` 工具保存到 USER.md 和 AGENT.md",
            "",
            "**重要提醒**:",
            "- AGENT.md、USER.md、RULE.md 已经在系统提示词中加载，无需再次读取。不要将这些文件名直接发送给用户",
            "- 能力介绍和交流风格选项都只要一行，保持精简",
            "- 不要问太多其他信息（职业、时区等可以后续自然了解）",
            "",
        ])
    
    return lines


def _build_context_files_section(context_files: List[ContextFile], language: str) -> List[str]:
    """构建项目上下文文件section"""
    if not context_files:
        return []
    
    # 检查是否有AGENT.md
    has_agent = any(
        f.path.lower().endswith('agent.md') or 'agent.md' in f.path.lower()
        for f in context_files
    )
    
    lines = [
        "# 项目上下文",
        "",
        "以下项目上下文文件已被加载：",
        "",
    ]
    
    if has_agent:
        lines.append("如果存在 `AGENT.md`，请体现其中定义的人格和语气。避免僵硬、模板化的回复；遵循其指导，除非有更高优先级的指令覆盖它。")
        lines.append("")
    
    # 添加每个文件的内容
    for file in context_files:
        lines.append(f"## {file.path}")
        lines.append("")
        lines.append(file.content)
        lines.append("")
    
    return lines


def _build_runtime_section(runtime_info: Dict[str, Any], language: str) -> List[str]:
    """构建运行时信息section - 支持动态时间"""
    if not runtime_info:
        return []
    
    lines = [
        "## 运行时信息",
        "",
    ]
    
    # Add current time if available
    # Support dynamic time via callable function
    if callable(runtime_info.get("_get_current_time")):
        try:
            time_info = runtime_info["_get_current_time"]()
            time_line = f"当前时间: {time_info['time']} {time_info['weekday']} ({time_info['timezone']})"
            lines.append(time_line)
            lines.append("")
        except Exception as e:
            logger.warning(f"[PromptBuilder] Failed to get dynamic time: {e}")
    elif runtime_info.get("current_time"):
        # Fallback to static time for backward compatibility
        time_str = runtime_info["current_time"]
        weekday = runtime_info.get("weekday", "")
        timezone = runtime_info.get("timezone", "")
        
        time_line = f"当前时间: {time_str}"
        if weekday:
            time_line += f" {weekday}"
        if timezone:
            time_line += f" ({timezone})"
        
        lines.append(time_line)
        lines.append("")
    
    # Add other runtime info
    runtime_parts = []
    if runtime_info.get("model"):
        runtime_parts.append(f"模型={runtime_info['model']}")
    if runtime_info.get("workspace"):
        runtime_parts.append(f"工作空间={runtime_info['workspace']}")
    # Only add channel if it's not the default "web"
    if runtime_info.get("channel") and runtime_info.get("channel") != "web":
        runtime_parts.append(f"渠道={runtime_info['channel']}")
    
    if runtime_parts:
        lines.append("运行时: " + " | ".join(runtime_parts))
        lines.append("")
    
    return lines
