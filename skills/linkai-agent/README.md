# LinkAI Agent Skill

这个 skill 允许你调用 LinkAI 平台上的多个应用(App)和工作流(Workflow)，通过简单的配置即可集成多个智能体能力。

## 特性

- ✅ **多应用支持** - 在一个配置文件中管理多个 LinkAI 应用/工作流
- ✅ **动态加载** - skill 系统加载时自动从 `config.json` 读取应用列表
- ✅ **自动技能描述** - 所有配置的应用会自动添加到技能描述中
- ✅ **模型切换** - 可以为每个请求指定不同的模型
- ✅ **知识库集成** - 支持应用绑定的知识库
- ✅ **插件能力** - 支持应用启用的各类插件
- ✅ **工作流执行** - 支持执行复杂的多步骤工作流

## 快速开始

### 1. 配置 API Key

```bash
env_config(action="set", key="LINKAI_API_KEY", value="your-linkai-api-key")
```

获取 API Key: https://link-ai.tech/console/interface

### 2. 配置应用列表

将 `config.json.template` 复制为 `config.json`：

```bash
cp config.json.template config.json
```

编辑 `config.json`，添加你的应用/工作流：

```json
{
  "apps": [
    {
      "app_code": "G7z6vKwp",
      "app_name": "通用助手",
      "app_description": "通用AI助手，可以回答各类问题"
    },
    {
      "app_code": "your_kb_app",
      "app_name": "产品文档助手",
      "app_description": "基于产品文档知识库的问答助手"
    },
    {
      "app_code": "your_workflow",
      "app_name": "数据分析工作流",
      "app_description": "执行数据清洗、分析和可视化的完整工作流"
    }
  ]
}
```

**注意：** 修改 `config.json` 后，Agent 在下次加载技能时会自动读取新配置。

### 3. 调用应用

```bash
bash scripts/call.sh "G7z6vKwp" "What is artificial intelligence?"
```

## 使用示例

### 基础调用

```bash
# 调用默认模型
bash scripts/call.sh "G7z6vKwp" "解释一下量子计算"
```

### 指定模型

```bash
# 使用 GPT-4.1 模型
bash scripts/call.sh "G7z6vKwp" "写一篇关于AI的文章" "LinkAI-4.1"

# 使用 DeepSeek 模型
bash scripts/call.sh "G7z6vKwp" "帮我写代码" "deepseek-chat"

# 使用 Claude 模型
bash scripts/call.sh "G7z6vKwp" "分析这段文本" "claude-4-sonnet"
```

### 调用工作流

```bash
# 工作流会按照配置的节点顺序执行
bash scripts/call.sh "workflow_code" "输入数据或问题"
```

## ⚠️ 重要提示

### 超时配置

LinkAI 应用（特别是视频/图片生成、复杂工作流）可能需要较长时间处理。

**脚本内置超时**：
- 默认：120 秒（适合大多数场景）
- 可通过第 5 个参数自定义：`bash scripts/call.sh <app_code> <question> "" "false" "180"`

**推荐超时时间**：
- **文本问答**：120 秒（默认）
- **图片生成**：120-180 秒
- **视频生成**：180-300 秒

Agent 调用时会自动设置合适的超时时间。

## 配置说明

### config.json 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `app_code` | string | 应用或工作流的唯一标识码，从 LinkAI 控制台获取 |
| `app_name` | string | 应用名称，会显示在技能描述中 |
| `app_description` | string | 应用功能描述，帮助 Agent 理解何时使用该应用 |

### 获取 app_code

1. 登录 [LinkAI 控制台](https://link-ai.tech/console)
2. 进入「应用管理」或「工作流管理」
3. 选择要集成的应用/工作流
4. 在应用详情页找到 `app_code`

## 支持的模型

LinkAI 支持多种主流 AI 模型：

**OpenAI 系列：**
- `LinkAI-4.1` - GPT-4.1 (1000K 上下文)
- `LinkAI-4.1-mini` - GPT-4.1 mini (1000K)
- `LinkAI-4.1-nano` - GPT-4.1 nano (1000K)
- `LinkAI-4o` - GPT-4o (128K)
- `LinkAI-4o-mini` - GPT-4o mini (128K)

**DeepSeek 系列：**
- `deepseek-chat` - DeepSeek-V3 对话模型 (64K)
- `deepseek-reasoner` - DeepSeek-R1 推理模型 (64K)

**Claude 系列：**
- `claude-4-sonnet` - Claude 4 Sonnet (200K)
- `claude-3-7-sonnet` - Claude 3.7 (200K)
- `claude-3-5-sonnet` - Claude 3.5 (200K)

**Google 系列：**
- `gemini-2.5-pro` - Gemini 2.5 Pro (1000K)
- `gemini-2.0-flash` - Gemini 2.0 Flash (1000K)

**国产模型：**
- `qwen3` - 通义千问3 (128K)
- `wenxin-4.5` - 文心一言4.5 (8K)
- `doubao-1.5-pro-256k` - 豆包1.5 (256K)
- `glm-4-plus` - 智谱GLM-4-Plus (4K)

完整模型列表：https://link-ai.tech/console/models

## 应用类型

### 1. 普通应用

配置了系统提示词和参数的标准对话应用，可以：
- 设置角色和性格
- 绑定知识库
- 启用插件（图像识别、网页搜索、代码执行等）

### 2. 知识库应用

基于特定知识库的问答应用，适合：
- 企业内部知识库
- 产品文档问答
- 客户支持

### 3. 工作流

多步骤的自动化流程，可以：
- 串联多个处理节点
- 条件分支
- 循环处理
- 调用外部 API

## 响应格式

### 成功响应

```json
{
  "app_code": "G7z6vKwp",
  "content": "人工智能（AI）是计算机科学的一个分支...",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 150,
    "total_tokens": 160
  }
}
```

### 错误响应

```json
{
  "error": "LinkAI API error",
  "message": "应用不存在",
  "response": { ... }
}
```

## 常见错误

### LINKAI_API_KEY environment variable is not set
**原因：** 未配置 API Key  
**解决：** 使用 `env_config` 工具设置 LINKAI_API_KEY

### 应用不存在 (402)
**原因：** app_code 不正确或应用已删除  
**解决：** 检查 app_code 是否正确，确认应用存在

### 无访问权限 (403)
**原因：** 尝试访问他人的私有应用  
**解决：** 确保应用是公开的或你是创建者

### 账号积分额度不足 (406)
**原因：** LinkAI 账户余额不足  
**解决：** 前往控制台充值

### 内容审核不通过 (409)
**原因：** 请求或响应包含敏感内容  
**解决：** 修改输入内容，避免敏感词

## 技术实现

### 自动技能描述生成

当 skill 系统加载 `linkai-agent` 时，会自动：
1. 读取 `config.json` 中的应用列表
2. 将每个应用的 name 和 description 动态添加到技能描述中
3. Agent 加载时会看到完整的应用列表

这是在 `agent/skills/loader.py` 中实现的特殊处理。

### 工作流程

```
用户配置 config.json
  ↓
Agent 启动/重新加载技能
  ↓
SkillLoader 检测到 linkai-agent
  ↓
动态读取 config.json
  ↓
生成包含所有应用描述的 description
  ↓
Agent 看到所有可用应用的完整信息
  ↓
用户请求触发
  ↓
Agent 根据描述选择合适的应用
  ↓
调用 call.sh <app_code> <question>
  ↓
LinkAI API 处理并返回结果
```

## 最佳实践

1. **清晰的描述** - 为每个应用写清晰、具体的描述，帮助 Agent 理解应用用途
2. **合理分工** - 不同应用负责不同领域，避免功能重叠
3. **无需重启** - 修改 config.json 后，Agent 下次加载技能时会自动更新
4. **模型选择** - 根据任务复杂度选择合适的模型
5. **知识库优化** - 为专业领域的应用绑定相关知识库

## 扩展用法

### 在 Agent 系统中使用

当 Agent 系统加载这个 skill 时，会自动从 `config.json` 读取应用列表并生成描述：

```
Call LinkAI apps/workflows. 通用助手(G7z6vKwp: 通用AI助手，可以回答各类问题); 产品文档助手(kb_app_001: 基于产品文档知识库的问答助手); 数据分析工作流(wf_002: 执行数据清洗、分析和可视化的完整工作流)
```

Agent 会根据用户问题自动选择最合适的应用进行调用。

## 相关链接

- LinkAI 平台: https://link-ai.tech
- API 文档: https://docs.link-ai.tech
- 控制台: https://link-ai.tech/console
- 模型列表: https://link-ai.tech/console/models
- 应用广场: https://link-ai.tech/square

## License

Part of the chatgpt-on-wechat project.
