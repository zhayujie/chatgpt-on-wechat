# CowAgent介绍

## 概述

Cow项目从简单的聊天机器人全面升级为超级智能助理 **CowAgent**，能够主动规思考和规划任务、拥有长期记忆、操作计算机和外部资源、创造和执行Skill，真正理解你并和你一起成长。CowAgent能够长期运行在个人电脑或服务器中，通过飞书、钉钉、企业微信、网页等多种方式进行交互。核心能力如下：

- **复杂任务规划**：能够理解复杂任务并自主规划执行，持续思考和调用工具直到完成目标，支持多轮推理和上下文理解
- **工具系统**：内置实现10+种工具，包括文件读写、bash终端、浏览器、定时任务、记忆管理等，通过Agent管理你的计算机或服务器
- **长期记忆**：自动将对话记忆持久化至本地文件和数据库中，包括全局记忆和天级记忆，支持关键词及向量检索
- **Skills系统**：新增Skill运行引擎，内置多种技能，并支持通过自然语言对话完成自定义Skills开发
- **多渠道和多模型支持**：支持在Web、飞书、钉钉、企微等多渠道与Agent交互，支持Claude、Gemini、OpenAI、GLM、MiniMax、Qwen 等多种国内外主流模型
- **安全和成本**：通过秘钥管理工具、提示词控制、系统权限等手段控制Agent的访问安全；通过最大记忆轮次、最大上下文token、工具执行步数对token成本进行限制


## 核心功能

### 1. 长期记忆

> 记忆系统让 Agent 能够长期记住重要信息。Agent 会在用户分享偏好、决策、事实等重要信息时主动存储，也会在对话达到一定长度时自动提取摘要。记忆分为核心记忆、天级记忆，支持语义搜索和向量检索的混合检索模式。


第一次启动Agent会主动向用户获取询问关键信息，并记录至工作空间 (默认为 ~/cow) 中的智能体设定、用户身份、记忆文件中。

在后续的长期对话中，Agent会在需要的时候智能记录或检索记忆，并对自身设定、用户偏好、记忆文件等进行不断更新，总结和记录经验和教训，真正实现自主思考和不断成长。

<img width="800" src="https://cdn.link-ai.tech/doc/20260203000455.png">



### 2. 任务规划和工具调用

工具是Agent访问操作系统资源的核心，Agent会根据任务需求智能选择和调用工具，完成文件读写、命令执行、定时任务等各类操作。内置工具的视线在项目的 `tools` 目录下。

**主要工具：** 文件读写编辑、Bash终端、浏览器、文件发送、定时调度、记忆搜索、环境配置等。

#### 1.1 终端和文件访问能力

针对操作系统的终端和文件的访问能力，是最基础和核心的工具，其他很多工具或技能都是基于基础工具进行扩展。用户可通过手机端与Agent交互，操作个人电脑或服务器上的资源：

<img width="800" src="https://cdn.link-ai.tech/doc/20260202181130.png">

#### 1.2 编程能力

基于编程能力和系统访问能力，Agent可以实现从信息搜索、图片等素材生成、编码、测试、部署、Nginx配置修改、发布的 Vibecoding 全流程，通过手机端简单的一句命令完成应用的快速demo：


<img width="800" src="https://cdn.link-ai.tech/doc/20260203121008.png">



#### 1.3 定时任务

基于 scheduler 工具实现动态定时任务，支持 **一次性任务、固定时间间隔、Cron表达式** 三种形式，任务触发可选择**固定消息发送** 或 **Agent动态任务** 执行两种模式，有很高灵活性：


<img width="800" src="https://cdn.link-ai.tech/doc/20260202195402.png">

同时你也可以通过自然语言快速查看和管理已有的定时任务。


#### 1.4 环境变量管理

技能所需要的秘钥存储在环境变量文件中，由 `env_config` 工具进行管理，你可以通过对话的方式更新秘钥，工具内置了安全保护和脱敏策略，会严格保护秘钥安全：

<img width="800" src="https://cdn.link-ai.tech/doc/20260202234939.png">

### 3. 技能系统

> 技能系统为Agent提供无限的扩展性，每个Skill由说明文件、运行脚本 (可选)、资源 (可选) 组成，描述如何完成特定类型的任务。通过Skill可以让Agent遵循说明完成复杂流程，调用各类工具或对接第三方系统等。

- **内置技能：** 在项目的`skills`目录下，包含技能创造器、网络搜索、图像识别（openai-image-vision）、LinkAI智能体、网页抓取等。内置Skill根据依赖条件 (API Key、系统命令等) 自动判断是否启用。通过技能创造器可以快速创建自定义技能。

- **自定义技能：** 由用户通过对话创建，存放在工作空间中 (`~/cow/skills/`)，基于自定义技能可以实现任何复杂的业务流程和第三方系统对接。


#### 3.1 创建技能

通过 `skill-creator` 技能可以通过对话的方式快速创建技能。你可以在与Agent的写作中让他对将某个工作流程固化为技能，或者把任意接口文档和示例发送给Agent，让他直接完成对接：

<img width="800" src="https://cdn.link-ai.tech/doc/20260202202247.png">


#### 3.2 搜索和图像识别

- **搜索技能：** 系统内置实现了 `bocha-search`(博查搜索)的Skill，依赖环境变量 `BOCHA_SEARCH_API_KEY`，可在[控制台](https://open.bochaai.com/)进行创建，并发送给Agent完成配置
- **图像识别技能：** 实现了 `openai-image-vision` 插件，可使用 gpt-4.1-mini、gpt-4.1 等图像识别模型。依赖秘钥 `OPENAI_API_KEY`，可通过config.json或env_config工具进行维护。

<img width="800" src="https://cdn.link-ai.tech/doc/20260202213219.png">


#### 3.3 三方知识库和插件

`linkai-agent` 技能可以将 [LinkAI](https://link-ai.tech/) 上的所有智能体作为skill交给Agent使用，并实现多智能体决策的效果。

使用方式：需通过对话的方式配置 `LINKAI_API_KEY`，或在config.json中添加 `linkai_api_key`。 并在 `skills/linkai-agent/config.json`中添加智能体说明，示例如下：

```json
{
  "apps": [
    {
      "app_code": "G7z6vKwp",
      "app_name": "LinkAI客服助手",
      "app_description": "当用户需要了解LinkAI平台相关问题时才选择该助手，基于LinkAI知识库进行回答"
    },
    {
      "app_code": "SFY5x7JR",
      "app_name": "内容创作助手",
      "app_description": "当用户需要创作图片或视频时才使用该助手，支持Nano Banana、Seedream、即梦、Veo、可灵等多种模型"
    }
  ]
}
```

Agent可根据智能体的名称和描述进行决策，并通过 app_code 调用接口访问对应的应用/工作流，通过该技能，可以灵活访问LinkAI平台上的智能体、知识库、插件等能力，实现效果如下：

<img width="750" src="https://cdn.link-ai.tech/doc/20260202234350.png">

注：需通过 `env_config` 配置 `LINKAI_API_KEY`，或在config.json中添加 `linkai_api_key` 配置。


## 使用方式

> 详细使用方式参考项目README.md文档进行

### 1.项目运行

在命令行中执行：

```bash
bash <(curl -sS https://cdn.link-ai.tech/code/cow/run.sh)
```

详细说明及后续程序管理参考：[项目启动脚本](https://github.com/zhayujie/chatgpt-on-wechat/wiki/CowAgentQuickStart)


### 2.模型选择

Agent模式推荐使用以下模型，可根据效果及成本综合选择：

- **MiniMax**: `MiniMax-M2.1`
- **GLM**: `glm-4.7`
- **Qwen**: `qwen3-max`
- **Claude**: `claude-sonnet-4-5`、`claude-sonnet-4-0`
- **Gemini**: `gemini-3-flash-preview`、`gemini-3-pro-preview`

详细模型配置方式参考 [README.md 模型说明](../README.md#模型说明)

### 3.Agent核心配置

Agent模式的核心配置项如下，在 `config.json` 中配置：

```bash
{
  "agent": true,                           # 是否启用Agent模式
  "agent_workspace": "~/cow",              # Agent工作空间路径
  "agent_max_context_tokens": 40000,       # 最大上下文tokens
  "agent_max_context_turns": 30,           # 最大上下文记忆轮次
  "agent_max_steps": 15                    # 单次任务最大决策步数
}
```

**配置说明：**

- `agent`: 设为 `true` 启用Agent模式，获得多轮工具决策、长期记忆、Skills等能力
- `agent_workspace`: 工作空间路径，用于存储 memory、skills、其他系统设定提示词
- `agent_max_context_tokens`: 上下文token上限，超出将自动丢弃最早的对话
- `agent_max_context_turns`: 上下文记忆轮次，每轮包括一次提问和回复
- `agent_max_steps`: 单次任务最大工具调用步数，防止无限循环


### 4.渠道接入

Agent支持在多种渠道中使用，只需修改 `config.json` 中的 `channel_type` 配置即可切换。

- **Web网页**：默认使用该渠道，运行后监听本地端口，通过浏览器访问
- **飞书接入**：[飞书接入文档](https://docs.link-ai.tech/cow/multi-platform/feishu)
- **钉钉接入**：[钉钉接入文档](https://docs.link-ai.tech/cow/multi-platform/dingtalk)
- **企业微信应用接入**：[企微应用文档](https://docs.link-ai.tech/cow/multi-platform/wechat-com)

更多渠道配置参考：[通道说明](../README.md#通道说明)
