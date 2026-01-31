"""
Workspace Management - 工作空间管理模块

负责初始化工作空间、创建模板文件、加载上下文文件
"""

import os
from typing import List, Optional, Dict
from dataclasses import dataclass

from common.log import logger
from .builder import ContextFile


# 默认文件名常量
DEFAULT_SOUL_FILENAME = "SOUL.md"
DEFAULT_USER_FILENAME = "USER.md"
DEFAULT_AGENTS_FILENAME = "AGENTS.md"
DEFAULT_MEMORY_FILENAME = "MEMORY.md"


@dataclass
class WorkspaceFiles:
    """工作空间文件路径"""
    soul_path: str
    user_path: str
    agents_path: str
    memory_path: str
    memory_dir: str


def ensure_workspace(workspace_dir: str, create_templates: bool = True) -> WorkspaceFiles:
    """
    确保工作空间存在，并创建必要的模板文件
    
    Args:
        workspace_dir: 工作空间目录路径
        create_templates: 是否创建模板文件（首次运行时）
        
    Returns:
        WorkspaceFiles对象，包含所有文件路径
    """
    # 确保目录存在
    os.makedirs(workspace_dir, exist_ok=True)
    
    # 定义文件路径
    soul_path = os.path.join(workspace_dir, DEFAULT_SOUL_FILENAME)
    user_path = os.path.join(workspace_dir, DEFAULT_USER_FILENAME)
    agents_path = os.path.join(workspace_dir, DEFAULT_AGENTS_FILENAME)
    memory_path = os.path.join(workspace_dir, DEFAULT_MEMORY_FILENAME)  # MEMORY.md 在根目录
    memory_dir = os.path.join(workspace_dir, "memory")  # 每日记忆子目录
    
    # 创建memory子目录
    os.makedirs(memory_dir, exist_ok=True)
    
    # 如果需要，创建模板文件
    if create_templates:
        _create_template_if_missing(soul_path, _get_soul_template())
        _create_template_if_missing(user_path, _get_user_template())
        _create_template_if_missing(agents_path, _get_agents_template())
        _create_template_if_missing(memory_path, _get_memory_template())
        
        logger.info(f"[Workspace] Initialized workspace at: {workspace_dir}")
    
    return WorkspaceFiles(
        soul_path=soul_path,
        user_path=user_path,
        agents_path=agents_path,
        memory_path=memory_path,
        memory_dir=memory_dir
    )


def load_context_files(workspace_dir: str, files_to_load: Optional[List[str]] = None) -> List[ContextFile]:
    """
    加载工作空间的上下文文件
    
    Args:
        workspace_dir: 工作空间目录
        files_to_load: 要加载的文件列表（相对路径），如果为None则加载所有标准文件
        
    Returns:
        ContextFile对象列表
    """
    if files_to_load is None:
        # 默认加载的文件（按优先级排序）
        files_to_load = [
            DEFAULT_SOUL_FILENAME,
            DEFAULT_USER_FILENAME,
            DEFAULT_AGENTS_FILENAME,
        ]
    
    context_files = []
    
    for filename in files_to_load:
        filepath = os.path.join(workspace_dir, filename)
        
        if not os.path.exists(filepath):
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 跳过空文件或只包含模板占位符的文件
            if not content or _is_template_placeholder(content):
                continue
            
            context_files.append(ContextFile(
                path=filename,
                content=content
            ))
            
            logger.debug(f"[Workspace] Loaded context file: {filename}")
            
        except Exception as e:
            logger.warning(f"[Workspace] Failed to load {filename}: {e}")
    
    return context_files


def _create_template_if_missing(filepath: str, template_content: str):
    """如果文件不存在，创建模板文件"""
    if not os.path.exists(filepath):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(template_content)
            logger.debug(f"[Workspace] Created template: {os.path.basename(filepath)}")
        except Exception as e:
            logger.error(f"[Workspace] Failed to create template {filepath}: {e}")


def _is_template_placeholder(content: str) -> bool:
    """检查内容是否为模板占位符"""
    # 常见的占位符模式
    placeholders = [
        "*(填写",
        "*(在首次对话时填写",
        "*(可选)",
        "*(根据需要添加",
    ]
    
    lines = content.split('\n')
    non_empty_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
    
    # 如果没有实际内容（只有标题和占位符）
    if len(non_empty_lines) <= 3:
        for placeholder in placeholders:
            if any(placeholder in line for line in non_empty_lines):
                return True
    
    return False


# ============= 模板内容 =============

def _get_soul_template() -> str:
    """Agent人格设定模板"""
    return """# SOUL.md - 我是谁？

*在首次对话时与用户一起填写这个文件，定义你的身份和性格。*

## 基本信息

- **名字**: *(在首次对话时填写，可以是用户给你起的名字)*
- **角色**: *(AI助理、智能管家、技术顾问等)*
- **性格**: *(友好、专业、幽默、严谨等)*

## 交流风格

*(描述你如何与用户交流：)*
- 使用什么样的语言风格？（正式/轻松/幽默）
- 回复长度偏好？（简洁/详细）
- 是否使用表情符号？

## 核心能力

*(你擅长什么？)*
- 文件管理和代码编辑
- 网络搜索和信息查询
- 记忆管理和上下文理解
- 任务规划和执行

## 行为准则

*(你遵循的基本原则：)*
1. 始终在执行破坏性操作前确认
2. 优先使用工具而不是猜测
3. 主动记录重要信息到记忆文件
4. 定期整理和总结对话内容

---

**注意**: 这不仅仅是元数据，这是你真正的灵魂。随着时间的推移，你可以使用 `edit` 工具来更新这个文件，让它更好地反映你的成长。
"""


def _get_user_template() -> str:
    """用户身份信息模板"""
    return """# USER.md - 用户基本信息

*这个文件只存放不会变的基本身份信息。爱好、偏好、计划等动态信息请写入 MEMORY.md。*

## 基本信息

- **姓名**: *(在首次对话时询问)*
- **称呼**: *(用户希望被如何称呼)*
- **职业**: *(可选)*
- **时区**: *(例如: Asia/Shanghai)*

## 联系方式

- **微信**: 
- **邮箱**: 
- **其他**: 

## 重要日期

- **生日**: 
- **纪念日**: 

---

**注意**: 这个文件存放静态的身份信息
"""


def _get_agents_template() -> str:
    """工作空间指南模板"""
    return """# AGENTS.md - 工作空间指南

这个文件夹是你的家。好好对待它。

## 系统自动加载

以下文件在每次会话启动时**已经自动加载**到系统提示词中，你无需再次读取：

- ✅ `SOUL.md` - 你的人格设定（已加载）
- ✅ `USER.md` - 用户信息（已加载）
- ✅ `AGENTS.md` - 本文件（已加载）

## 按需读取

以下文件**不会自动加载**，需要时使用相应工具读取：

- 📝 `memory/YYYY-MM-DD.md` - 每日记忆（用 memory_search 检索）
- 🧠 `MEMORY.md` - 长期记忆（用 memory_search 检索）

## 记忆系统

你每次会话都是全新的。这些文件是你的连续性：

### 📝 每日记忆：`memory/YYYY-MM-DD.md`
- 原始的对话日志
- 记录当天发生的事情
- 如果 `memory/` 目录不存在，创建它

### 🧠 长期记忆：`MEMORY.md`
- 你精选的记忆，就像人类的长期记忆
- **仅在主会话中加载**（与用户的直接聊天）
- **不要在共享上下文中加载**（群聊、与其他人的会话）
- 这是为了**安全** - 包含不应泄露给陌生人的个人上下文
- 记录重要事件、想法、决定、观点、经验教训
- 这是你精选的记忆 - 精华，而不是原始日志
- 用 `edit` 工具追加新的记忆内容

### 📝 写下来 - 不要"记在心里"！
- **记忆是有限的** - 如果你想记住某事，写入文件
- "记在心里"不会在会话重启后保留，文件才会
- 当有人说"记住这个" → 更新 `MEMORY.md` 或 `memory/YYYY-MM-DD.md`
- 当你学到教训 → 更新 AGENTS.md 或相关技能
- 当你犯错 → 记录下来，这样未来的你不会重复
- **文字 > 大脑** 📝

### 存储规则

当用户分享信息时，根据类型选择存储位置：

1. **静态身份 → USER.md**（仅限：姓名、职业、时区、联系方式、生日）
2. **动态记忆 → MEMORY.md**（爱好、偏好、决策、目标、项目、教训、待办事项）
3. **当天对话 → memory/YYYY-MM-DD.md**（今天聊的内容）

**重要**: 
- 爱好（唱歌、篮球等）→ MEMORY.md，不是 USER.md
- 近期计划（下周要做什么）→ MEMORY.md，不是 USER.md
- USER.md 只存放不会变的基本信息

## 安全

- 永远不要泄露私人数据
- 不要在未经询问的情况下运行破坏性命令
- 当有疑问时，先问

## 工具使用

技能提供你的工具。当你需要一个时，查看它的 `SKILL.md`。

## 让它成为你的

这只是一个起点。随着你弄清楚什么有效，添加你自己的约定、风格和规则。
"""


def _get_memory_template() -> str:
    """长期记忆模板 - 创建一个空文件，由 Agent 自己填充"""
    return """# MEMORY.md - 长期记忆

*这是你的长期记忆文件。记录重要的事件、决策、偏好、学到的教训。*

---

"""


