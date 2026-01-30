# Bug Fix: Skills 无法从 Workspace 加载

## 🐛 问题描述

用户创建的 skills（位于 `~/cow/skills/`）没有被 Agent 加载，只有项目内置的 skills（位于 `项目/skills/`）被加载。

**症状**：
```
[INFO] Loaded 1 skills from all sources  # 只加载了 skill-creator
[INFO] SkillManager: Loaded 1 skills
```

**预期**：
```
[INFO] Loaded 2 skills from all sources  # 应该加载 skill-creator + desktop-explorer
[INFO] SkillManager: Loaded 2 skills
```

## 🔍 根因分析

### 问题定位

通过逐步调试发现：

1. **Skills 加载逻辑正确** ✅
   - `SkillLoader.load_all_skills()` 能正确加载两个目录
   - `SkillManager` 构造函数正确接收 `workspace_dir` 参数
   
2. **Agent 构造函数正确** ✅
   - `Agent.__init__()` 正确接收 `workspace_dir` 和 `enable_skills` 参数
   - 能正确创建 `SkillManager`

3. **`AgentBridge._init_default_agent()` 正确** ✅
   - 正确读取 `agent_workspace` 配置
   - 正确调用 `create_agent()` 并传递 `workspace_dir` 等参数

4. **`AgentBridge.create_agent()` 有问题** ❌
   - **虽然接收了 `workspace_dir` 等参数（在 `**kwargs` 中）**
   - **但没有传递给 `Agent` 构造函数！**

### 问题代码

```python
# bridge/agent_bridge.py:196-203

def create_agent(self, system_prompt: str, tools: List = None, **kwargs) -> Agent:
    ...
    self.agent = Agent(
        system_prompt=system_prompt,
        description=kwargs.get("description", "AI Super Agent"),
        model=model,
        tools=tools,
        max_steps=kwargs.get("max_steps", 15),
        output_mode=kwargs.get("output_mode", "logger")
        # ❌ 缺少: workspace_dir, enable_skills, memory_manager 等参数！
    )
```

## ✅ 修复方案

### 修改文件

`bridge/agent_bridge.py` 的 `create_agent()` 方法

### 修改内容

```python
def create_agent(self, system_prompt: str, tools: List = None, **kwargs) -> Agent:
    ...
    self.agent = Agent(
        system_prompt=system_prompt,
        description=kwargs.get("description", "AI Super Agent"),
        model=model,
        tools=tools,
        max_steps=kwargs.get("max_steps", 15),
        output_mode=kwargs.get("output_mode", "logger"),
        workspace_dir=kwargs.get("workspace_dir"),  # ✅ 新增
        enable_skills=kwargs.get("enable_skills", True),  # ✅ 新增
        memory_manager=kwargs.get("memory_manager"),  # ✅ 新增
        max_context_tokens=kwargs.get("max_context_tokens"),  # ✅ 新增
        context_reserve_tokens=kwargs.get("context_reserve_tokens")  # ✅ 新增
    )
    
    # ✅ 新增：输出详细的 skills 加载日志
    if self.agent.skill_manager:
        logger.info(f"[AgentBridge] SkillManager initialized:")
        logger.info(f"[AgentBridge]   - Managed dir: {self.agent.skill_manager.managed_skills_dir}")
        logger.info(f"[AgentBridge]   - Workspace dir: {self.agent.skill_manager.workspace_dir}")
        logger.info(f"[AgentBridge]   - Total skills: {len(self.agent.skill_manager.skills)}")
        for skill_name in self.agent.skill_manager.skills.keys():
            logger.info(f"[AgentBridge]     * {skill_name}")
    
    return self.agent
```

## 📊 修复后的效果

### 启动日志

```
[INFO][agent_bridge.py:228] - [AgentBridge] Workspace initialized at: /Users/zhayujie/cow
[INFO][loader.py:219] - Loaded 2 skills from all sources  # ✅ 现在是 2 个
[INFO][manager.py:62] - SkillManager: Loaded 2 skills
[INFO][agent.py:60] - Initialized SkillManager with 2 skills
[INFO][agent_bridge.py:xxx] - [AgentBridge] SkillManager initialized:
[INFO][agent_bridge.py:xxx] - [AgentBridge]   - Managed dir: /path/to/project/skills
[INFO][agent_bridge.py:xxx] - [AgentBridge]   - Workspace dir: /Users/zhayujie/cow
[INFO][agent_bridge.py:xxx] - [AgentBridge]   - Total skills: 2
[INFO][agent_bridge.py:xxx] - [AgentBridge]     * skill-creator
[INFO][agent_bridge.py:xxx] - [AgentBridge]     * desktop-explorer
```

### Skills 来源

| Skill Name | 来源目录 | 说明 |
|---|---|---|
| `skill-creator` | `项目/skills/` | 项目内置，用于创建新 skills |
| `desktop-explorer` | `~/cow/skills/` | 用户创建的 skill |

## 🎯 总结

### 问题
`create_agent()` 方法没有将 `workspace_dir` 等关键参数传递给 `Agent` 构造函数，导致 Agent 无法加载用户工作空间的 skills。

### 修复
在 `create_agent()` 方法中添加所有必要的参数传递。

### 影响范围
- ✅ Skills 加载
- ✅ Memory 管理器传递
- ✅ 上下文管理参数传递

### 测试方法
1. 启动 Agent
2. 检查日志中是否显示 "Loaded 2 skills from all sources"
3. 检查是否列出了 `skill-creator` 和 `desktop-explorer` 两个 skills

---

**状态**: ✅ 已修复  
**测试**: ⏳ 待测试  
**日期**: 2026-01-30
