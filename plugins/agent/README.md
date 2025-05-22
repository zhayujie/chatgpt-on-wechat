# AgentMesh Plugin

这个插件集成了 AgentMesh 多智能体框架，允许用户通过简单的命令使用多智能体团队来完成各种任务。

## 功能介绍

AgentMesh 是一个开源的多智能体平台，提供开箱即用的 Agent 开发框架、多 Agent 间的协同策略、任务规划和自主决策能力。通过这个插件，你可以：

- 使用预配置的智能体团队处理复杂任务
- 利用多智能体协作能力解决问题
- 访问各种工具，如搜索引擎、浏览器、文件系统等

## 安装

1. 确保已安装 AgentMesh SDK：

```bash
pip install agentmesh-sdk>=0.1.0
```

2. 如需使用浏览器工具，还需安装：

```bash
pip install browser-use>=0.1.40
playwright install
```

## 配置

插件从项目根目录的 `config.yaml` 文件中读取配置。请确保该文件包含正确的团队配置。

配置示例：

```yaml
teams:
  general_team:
    description: "通用智能体团队，擅长于搜索、研究和执行各种任务"
    model: "gpt-4o"
    max_steps: 20
    agents:
      - name: "通用助手"
        description: "全能的通用智能体"
        system_prompt: "你是全能的通用智能体，可以帮助用户解决工作、生活、学习上的任何问题，以及使用工具解决各类复杂问题"
        tools: ["google_search", "calculator", "current_time"]
```

## 使用方法

使用 `$agent` 前缀触发插件，支持以下命令：

- `$agent teams` - 列出可用的团队
- `$agent use [team_name] [task]` - 使用特定团队执行任务
- `$agent [task]` - 使用默认团队执行任务

### 示例

```
$agent teams
$agent use general_team 帮我分析多智能体技术发展趋势
$agent 帮我查看当前文件夹路径
```

## 工具支持

AgentMesh 支持多种工具，包括但不限于：

- `calculator`: 数学计算工具
- `current_time`: 获取当前时间
- `browser`: 浏览器操作工具
- `google_search`: 搜索引擎
- `file_save`: 文件保存工具
- `terminal`: 终端命令执行工具

## 注意事项

1. 确保 `config.yaml` 文件中包含正确的团队配置
2. 如果需要使用浏览器工具，请确保安装了相关依赖
