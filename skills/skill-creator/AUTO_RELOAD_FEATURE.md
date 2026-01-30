# 技能自动重载功能

## ✨ 新功能：创建技能后自动刷新

### 📋 问题

**之前的行为**：
1. 用户通过 skill-creator 创建新技能
2. bash 工具执行 `init_skill.py` 成功
3. 新技能被创建在 `~/cow/skills/` 目录
4. ❌ **但 Agent 不知道有新技能**
5. ❌ **需要重启 Agent 才能加载新技能**

### ✅ 解决方案

在 `agent/protocol/agent_stream.py` 的 `_execute_tool()` 方法中添加自动检测和刷新逻辑：

```python
def _execute_tool(self, tool_call: Dict) -> Dict[str, Any]:
    ...
    # Execute tool
    result: ToolResult = tool.execute_tool(arguments)
    
    # Auto-refresh skills after skill creation
    if tool_name == "bash" and result.status == "success":
        command = arguments.get("command", "")
        if "init_skill.py" in command and self.agent.skill_manager:
            logger.info("🔄 Detected skill creation, refreshing skills...")
            self.agent.refresh_skills()
            logger.info(f"✅ Skills refreshed! Now have {len(self.agent.skill_manager.skills)} skills")
    ...
```

### 🎯 工作原理

1. **检测技能创建**：
   - 监听 bash 工具的执行
   - 检查命令中是否包含 `init_skill.py`
   - 检查执行是否成功

2. **自动刷新**：
   - 调用 `agent.refresh_skills()`
   - `SkillManager` 重新扫描所有技能目录
   - 加载新创建的技能

3. **即时可用**：
   - 在同一个对话中
   - 下一轮对话就能使用新技能
   - 无需重启 Agent ✅

### 📊 使用效果

**创建技能的对话**：
```
用户: 创建一个新技能叫 weather-api

Agent:
  第1轮: 使用 bash 工具运行 init_skill.py
  🔄 Detected skill creation, refreshing skills...
  ✅ Skills refreshed! Now have 2 skills
  
  第2轮: 回复用户 "技能 weather-api 已创建成功"

用户: 使用 weather-api 技能查询天气

Agent:
  第1轮: ✅ 直接使用 weather-api 技能（无需重启！）
```

### 🔍 刷新范围

`refresh_skills()` 会重新加载：
- ✅ 项目内置技能目录：`项目/skills/`
- ✅ 用户工作空间技能：`~/cow/skills/`
- ✅ 任何额外配置的技能目录

### ⚡ 性能影响

- **触发时机**：只在检测到 `init_skill.py` 执行成功后
- **频率**：极低（只有创建新技能时）
- **耗时**：< 100ms（扫描和解析 SKILL.md 文件）
- **影响**：几乎可以忽略

### 🐛 边界情况

1. **技能创建失败**：
   - `result.status != "success"`
   - 不会触发刷新
   - 避免无效刷新

2. **没有 SkillManager**：
   - `self.agent.skill_manager` 为 None
   - 不会触发刷新
   - 避免空指针异常

3. **非技能相关的 bash 命令**：
   - 命令中不包含 `init_skill.py`
   - 不会触发刷新
   - 避免不必要的性能开销

### 🔮 未来改进

可以扩展到其他场景：

1. **技能编辑后刷新**：
   - 检测 `SKILL.md` 被修改
   - 自动刷新对应的技能

2. **技能删除后刷新**：
   - 检测技能目录被删除
   - 自动移除技能

3. **热重载模式**：
   - 文件监听器（watchdog）
   - 实时检测技能文件变化
   - 自动刷新

## 📝 相关代码

### Agent.refresh_skills()

```python
# agent/protocol/agent.py

def refresh_skills(self):
    """Reload all skills from configured directories."""
    if self.skill_manager:
        self.skill_manager.refresh_skills()
```

### SkillManager.refresh_skills()

```python
# agent/skills/manager.py

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
    
    logger.info(f"SkillManager: Loaded {len(self.skills)} skills")
```

---

**状态**: ✅ 已实现  
**测试**: ⏳ 待测试  
**日期**: 2026-01-30
