<p align="center"><img src= "https://github.com/user-attachments/assets/eca9a9ec-8534-4615-9e0f-96c5ac1d10a3" alt="Chatgpt-on-Wechat" width="550" /></p>

<p align="center">
   <a href="https://github.com/zhayujie/chatgpt-on-wechat/releases/latest"><img src="https://img.shields.io/github/v/release/zhayujie/chatgpt-on-wechat" alt="Latest release"></a>
  <a href="https://github.com/zhayujie/chatgpt-on-wechat/blob/master/LICENSE"><img src="https://img.shields.io/github/license/zhayujie/chatgpt-on-wechat" alt="License: MIT"></a>
  <a href="https://github.com/zhayujie/chatgpt-on-wechat"><img src="https://img.shields.io/github/stars/zhayujie/chatgpt-on-wechat?style=flat-square" alt="Stars"></a> <br/>
</p>

**CowAgent** 是基于大模型的超级AI助理，能够主动思考和任务规划、操作计算机和外部资源、创造和执行Skills、拥有长期记忆并不断成长。CowAgent 支持灵活切换多种模型，能处理文本、语音、图片、文件等多模态消息，可接入网页、飞书、钉钉、企业微信应用、微信公众号中使用，7*24小时运行于你的个人电脑或服务器中。

📖能力介绍：[CowAgent 2.0](/docs/agent.md)

# 简介

> 该项目既是一个可以开箱即用的超级AI助理，也是一个支持高扩展的Agent框架，可以通过为项目扩展大模型接口、接入渠道、内置工具、Skills系统来灵活实现各种定制需求。核心能力如下：

-  ✅  **复杂任务规划**：能够理解复杂任务并自主规划执行，持续思考和调用工具直到完成目标，支持通过工具操作访问文件、终端、浏览器、定时任务等系统资源
-  ✅  **长期记忆：** 自动将对话记忆持久化至本地文件和数据库中，包括全局记忆和天级记忆，支持关键词及向量检索
-  ✅  **技能系统：** 实现了Skills创建和运行的引擎，内置多种技能，并支持通过自然语言对话完成自定义Skills开发
-  ✅  **多模态消息：** 支持对文本、图片、语音、文件等多类型消息进行解析、处理、生成、发送等操作
-  ✅  **多模型接入：** 支持OpenAI, Claude, Gemini, DeepSeek, MiniMax、GLM、Qwen、Kimi等国内外主流模型厂商
-  ✅  **多端部署：** 支持运行在本地计算机或服务器，可集成到网页、飞书、钉钉、微信公众号、企业微信应用中使用
-  ✅  **知识库：** 集成企业知识库能力，让Agent成为专属数字员工，基于[LinkAI](https://link-ai.tech)平台实现

## 声明

1. 本项目遵循 [MIT开源协议](/LICENSE)，主要用于技术研究和学习，使用本项目时需遵守所在地法律法规、相关政策以及企业章程，禁止用于任何违法或侵犯他人权益的行为。任何个人、团队和企业，无论以何种方式使用该项目、对何对象提供服务，所产生的一切后果，本项目均不承担任何责任
2. 成本与安全：Agent模式下Token使用量高于普通对话模式，请根据效果及成本综合选择模型。Agent具有访问所在操作系统的能力，请谨慎选择项目部署环境。同时项目也会持续升级安全机制、并降低模型消耗成本

## 演示

使用说明(Agent模式)：[CowAgent介绍](/docs/agent.md)

DEMO视频(对话模式)：https://cdn.link-ai.tech/doc/cow_demo.mp4

## 社区

添加小助手微信加入开源项目交流群：

<img width="140" src="https://img-1317903499.cos.ap-guangzhou.myqcloud.com/docs/open-community.png">

<br/>

# 企业服务

<a href="https://link-ai.tech" target="_blank"><img width="720" src="https://cdn.link-ai.tech/image/link-ai-intro.jpg"></a>

> [LinkAI](https://link-ai.tech/) 是面向企业和开发者的一站式AI智能体平台，聚合多模态大模型、知识库、Agent 插件、工作流等能力，支持一键接入主流平台并进行管理，支持SaaS、私有化部署等多种模式。
>
> LinkAI 目前已在智能客服、私域运营、企业效率助手等场景积累了丰富的AI解决方案，在消费、健康、文教、科技制造等各行业沉淀了大模型落地应用的最佳实践，致力于帮助更多企业和开发者拥抱 AI 生产力。

**产品咨询和企业服务** 可联系产品客服：

<img width="150" src="https://cdn.link-ai.tech/portal/linkai-customer-service.png">

<br/>

# 🏷 更新日志

>**2026.02.03：** [2.0.0版本](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/2.0.0)，正式升级为超级Agent助理，支持多轮任务决策、具备长期记忆、实现多种系统工具、支持Skills框架，新增多种模型并优化了接入渠道。

>**2025.05.23：** [1.7.6版本](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.7.6) 优化web网页channel、新增 [AgentMesh](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/plugins/agent/README.md)多智能体插件、百度语音合成优化、企微应用`access_token`获取优化、支持`claude-4-sonnet`和`claude-4-opus`模型

>**2025.04.11：** [1.7.5版本](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.7.5) 新增支持 [wechatferry](https://github.com/zhayujie/chatgpt-on-wechat/pull/2562) 协议、新增 deepseek 模型、新增支持腾讯云语音能力、新增支持 ModelScope 和 Gitee-AI API接口

>**2024.12.13：** [1.7.4版本](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.7.4) 新增 Gemini 2.0 模型、新增web channel、解决内存泄漏问题、解决 `#reloadp` 命令重载不生效问题

>**2024.10.31：** [1.7.3版本](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.7.3) 程序稳定性提升、数据库功能、Claude模型优化、linkai插件优化、离线通知

更多更新历史请查看: [更新日志](/docs/release/history.md)

<br/>

# 🚀 快速开始

项目提供了一键安装、配置、启动、管理程序的脚本，推荐使用脚本快速运行，也可以根据下文中的详细指引一步步安装运行。

在终端执行以下命令：

```bash
bash <(curl -sS https://cdn.link-ai.tech/code/cow/run.sh)
```

脚本使用说明：[一键运行脚本](https://github.com/zhayujie/chatgpt-on-wechat/wiki/CowAgentQuickStart)


## 一、准备

### 1. 模型API

项目支持国内外主流厂商的模型接口，可选模型及配置说明参考：[模型说明](#模型说明)。

> 注：Agent模式下推荐使用以下模型，可根据效果及成本综合选择：GLM(glm-4.7)、MiniMAx(MiniMax-M2.1)、Qwen(qwen3-max)、Claude(claude-opus-4-6、claude-sonnet-4-5、claude-sonnet-4-0)、Gemini(gemini-3-flash-preview、gemini-3-pro-preview)

同时支持使用 **LinkAI平台** 接口，可灵活切换 OpenAI、Claude、Gemini、DeepSeek、Qwen、Kimi 等多种常用模型，并支持知识库、工作流、插件等Agent能力，参考 [接口文档](https://docs.link-ai.tech/platform/api)。

### 2.环境安装

支持 Linux、MacOS、Windows 操作系统，可在个人计算机及服务器上运行，需安装 `Python`，Python版本需在3.7 ~ 3.12 之间，推荐使用3.9版本。

> 注意：Agent模式推荐使用源码运行，若选择Docker部署则无需安装python环境和下载源码，可直接快进到下一节。

**(1) 克隆项目代码：**

```bash
git clone https://github.com/zhayujie/chatgpt-on-wechat
cd chatgpt-on-wechat/
```

若遇到网络问题可使用国内仓库地址：https://gitee.com/zhayujie/chatgpt-on-wechat

**(2) 安装核心依赖 (必选)：**

```bash
pip3 install -r requirements.txt
```

**(3) 拓展依赖 (可选，建议安装)：**

```bash
pip3 install -r requirements-optional.txt
```
如果某项依赖安装失败可注释掉对应的行后重试。

## 二、配置

配置文件的模板在根目录的`config-template.json`中，需复制该模板创建最终生效的 `config.json` 文件：

```bash
  cp config-template.json config.json
```

然后在`config.json`中填入配置，以下是对默认配置的说明，可根据需要进行自定义修改（注意实际使用时请去掉注释，保证JSON格式的规范）：

```bash
# config.json 文件内容示例
{
  "channel_type": "web",                                      # 接入渠道类型，默认为web，支持修改为:feishu,dingtalk,wechatcom_app,terminal,wechatmp,wechatmp_service
  "model": "MiniMax-M2.1",                                    # 模型名称
  "minimax_api_key": "",                                      # MiniMax API Key
  "zhipu_ai_api_key": "",                                     # 智谱GLM API Key
  "dashscope_api_key": "",                                    # 百炼(通义千问)API Key
  "claude_api_key": "",                                       # Claude API Key
  "claude_api_base": "https://api.anthropic.com/v1",          # Claude API 地址，修改可接入三方代理平台
  "gemini_api_key": "",                                       # Gemini API Key
  "gemini_api_base": "https://generativelanguage.googleapis.com", # Gemini API地址
  "open_ai_api_key": "",                                      # OpenAI API Key
  "open_ai_api_base": "https://api.openai.com/v1",            # OpenAI API 地址
  "linkai_api_key": "",                                       # LinkAI API Key
  "proxy": "",                                                # 代理客户端的ip和端口，国内环境需要开启代理的可填写该项，如 "127.0.0.1:7890"
  "speech_recognition": false,                                # 是否开启语音识别
  "group_speech_recognition": false,                          # 是否开启群组语音识别
  "voice_reply_voice": false,                                 # 是否使用语音回复语音
  "use_linkai": false,                                        # 是否使用LinkAI接口，默认关闭，设置为true后可对接LinkAI平台接口
  "agent": true,                                              # 是否启用Agent模式，启用后拥有多轮工具决策、长期记忆、Skills能力等
  "agent_workspace": "~/cow",                                 # Agent的工作空间路径，用于存储memory、skills、系统设定等
  "agent_max_context_tokens": 40000,                          # Agent模式下最大上下文tokens，超出将自动丢弃最早的上下文
  "agent_max_context_turns": 30,                              # Agent模式下最大上下文记忆轮次，每轮包括一次用户提问和AI回复
  "agent_max_steps": 15                                       # Agent模式下单次任务的最大决策步数，超出后将停止继续调用工具
}
```

**配置补充说明:** 

<details>
<summary>1. 语音配置</summary>

+ 添加 `"speech_recognition": true` 将开启语音识别，默认使用openai的whisper模型识别为文字，同时以文字回复，该参数仅支持私聊 (注意由于语音消息无法匹配前缀，一旦开启将对所有语音自动回复，支持语音触发画图)；
+ 添加 `"group_speech_recognition": true` 将开启群组语音识别，默认使用openai的whisper模型识别为文字，同时以文字回复，参数仅支持群聊 (会匹配group_chat_prefix和group_chat_keyword, 支持语音触发画图)；
+ 添加 `"voice_reply_voice": true` 将开启语音回复语音（同时作用于私聊和群聊）
</details>

<details>
<summary>2. 其他配置</summary>

+ `model`: 模型名称，Agent模式下推荐使用 `glm-4.7`、`MiniMax-M2.1`、`qwen3-max`、`claude-opus-4-6`、`claude-sonnet-4-5`、`claude-sonnet-4-0`、`gemini-3-flash-preview`、`gemini-3-pro-preview`，全部模型名称参考[common/const.py](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/common/const.py)文件
+ `character_desc`：普通对话模式下的机器人系统提示词。在Agent模式下该配置不生效，由工作空间中的文件内容构成。
+ `subscribe_msg`：订阅消息，公众号和企业微信channel中请填写，当被订阅时会自动回复， 可使用特殊占位符。目前支持的占位符有{trigger_prefix}，在程序中它会自动替换成bot的触发词。
</details>

<details>
<summary>5. LinkAI配置</summary>

+ `use_linkai`: 是否使用LinkAI接口，默认关闭，设置为true后可对接LinkAI平台，使用知识库、工作流、插件等能力, 参考[接口文档](https://docs.link-ai.tech/platform/api/chat)
+ `linkai_api_key`: LinkAI Api Key，可在 [控制台](https://link-ai.tech/console/interface) 创建
+ `linkai_app_code`: LinkAI 应用或工作流的code，选填，普通对话模式中使用。
</details>

注：全部配置项说明可在 [`config.py`](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/config.py) 文件中查看。

## 三、运行

### 1.本地运行

如果是个人计算机 **本地运行**，直接在项目根目录下执行：

```bash
python3 app.py         # windows环境下该命令通常为 python app.py
```

运行后默认会启动web服务，可通过访问 `http://localhost:9899/chat` 在网页端对话。

如果需要接入其他应用通道只需修改 `config.json` 配置文件中的 `channel_type` 参数，详情参考：[通道说明](#通道说明)。


### 2.服务器部署

在服务器中可使用 `nohup` 命令在后台运行程序：

```bash
nohup python3 app.py & tail -f nohup.out
```

执行后程序运行于服务器后台，可通过 `ctrl+c` 关闭日志，不会影响后台程序的运行。使用 `ps -ef | grep app.py | grep -v grep` 命令可查看运行于后台的进程，如果想要重新启动程序可以先 `kill` 掉对应的进程。 日志关闭后如果想要再次打开只需输入 `tail -f nohup.out`。 

此外，项目的 `scripts` 目录下有一键运行、关闭程序的脚本供使用。 运行后默认channel为web，通过可以通过修改配置文件进行切换。


### 3.Docker部署

使用docker部署无需下载源码和安装依赖，只需要获取 `docker-compose.yml` 配置文件并启动容器即可。Agent模式下更推荐使用源码进行部署，以获得更多系统访问能力。

> 前提是需要安装好 `docker` 及 `docker-compose`，安装成功后执行 `docker -v` 和 `docker-compose version` (或 `docker compose version`) 可查看到版本号。安装地址为 [docker官网](https://docs.docker.com/engine/install/) 。

**(1) 下载 docker-compose.yml 文件**

```bash
wget https://cdn.link-ai.tech/code/cow/docker-compose.yml
```

下载完成后打开 `docker-compose.yml` 填写所需配置，例如 `CHANNEL_TYPE`、`OPEN_AI_API_KEY` 和等配置。

**(2) 启动容器**

在 `docker-compose.yml` 所在目录下执行以下命令启动容器：

```bash
sudo docker compose up -d         # 若docker-compose为 1.X 版本，则执行 `sudo  docker-compose up -d`
```

运行命令后，会自动取 [docker hub](https://hub.docker.com/r/zhayujie/chatgpt-on-wechat) 拉取最新release版本的镜像。当执行 `sudo docker ps` 能查看到 NAMES 为 chatgpt-on-wechat 的容器即表示运行成功。最后执行以下命令可查看容器的运行日志：

```bash
sudo docker logs -f chatgpt-on-wechat
```

**(3) 插件使用**

如果需要在docker容器中修改插件配置，可通过挂载的方式完成，将 [插件配置文件](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/plugins/config.json.template)
重命名为 `config.json`，放置于 `docker-compose.yml` 相同目录下，并在 `docker-compose.yml` 中的 `chatgpt-on-wechat` 部分下添加 `volumes` 映射:

```
volumes:
  - ./config.json:/app/plugins/config.json
```
**注**：使用docker方式部署的详细教程可以参考：[docker部署CoW项目](https://www.wangpc.cc/ai/docker-deploy-cow/)


## 模型说明

以下对所有可支持的模型的配置和使用方法进行说明，模型接口实现在项目的 `models/` 目录下。

<details>
<summary>OpenAI</summary>

1. API Key创建：在 [OpenAI平台](https://platform.openai.com/api-keys) 创建API Key

2. 填写配置

```json
{
    "model": "gpt-4.1-mini",
    "open_ai_api_key": "YOUR_API_KEY",
    "open_ai_api_base": "https://api.openai.com/v1",
    "bot_type": "chatGPT"
}
```

 - `model`: 与OpenAI接口的 [model参数](https://platform.openai.com/docs/models) 一致，支持包括 o系列、gpt-5.2、gpt-5.1、gpt-4.1等系列模型
 - `open_ai_api_base`: 如果需要接入第三方代理接口，可通过修改该参数进行接入
 - `bot_type`: 使用OpenAI相关模型时无需填写。当使用第三方代理接口接入Claude等非OpenAI官方模型时，该参数设为 `chatGPT`
</details>

<details>
<summary>LinkAI</summary>

1. API Key创建：在 [LinkAI平台](https://link-ai.tech/console/interface) 创建API Key 

2. 填写配置

```json
{
    "use_linkai": true,
    "linkai_api_key": "YOUR API KEY",
    "linkai_app_code": "YOUR APP CODE"
}
```

+ `use_linkai`: 是否使用LinkAI接口，默认关闭，设置为true后可对接LinkAI平台的智能体，使用知识库、工作流、数据库、MCP插件等丰富的Agent能力
+ `linkai_api_key`: LinkAI平台的API Key，可在 [控制台](https://link-ai.tech/console/interface) 中创建
+ `linkai_app_code`: LinkAI智能体 (应用或工作流) 的code，选填，普通对话模式可用。智能体创建可参考 [说明文档](https://docs.link-ai.tech/platform/quick-start)
+ `model`: model字段填写空则直接使用智能体的模型，可在平台中灵活切换，[模型列表](https://link-ai.tech/console/models)中的全部模型均可使用
</details>

<details>
<summary>MiniMax</summary>

方式一：官方接入，配置如下(推荐)：

```json
{
    "model": "MiniMax-M2.1",
    "minimax_api_key": ""
}
```
 - `model`: 可填写 `MiniMax-M2.1、MiniMax-M2.1-lightning、MiniMax-M2、abab6.5-chat` 等
 - `minimax_api_key`：MiniMax平台的API-KEY，在 [控制台](https://platform.minimaxi.com/user-center/basic-information/interface-key) 创建

方式二：OpenAI兼容方式接入，配置如下：
```json
{
  "bot_type": "chatGPT",
  "model": "MiniMax-M2.1",
  "open_ai_api_base": "https://api.minimaxi.com/v1",
  "open_ai_api_key": ""
}
```
- `bot_type`: OpenAI兼容方式
- `model`: 可填 `MiniMax-M2.1、MiniMax-M2.1-lightning、MiniMax-M2`，参考[API文档](https://platform.minimaxi.com/document/%E5%AF%B9%E8%AF%9D?key=66701d281d57f38758d581d0#QklxsNSbaf6kM4j6wjO5eEek)
- `open_ai_api_base`: MiniMax平台API的 BASE URL
- `open_ai_api_key`: MiniMax平台的API-KEY
</details>

<details>
<summary>智谱AI (GLM)</summary>

方式一：官方接入，配置如下(推荐)：

```json
{
  "model": "glm-4.7",
  "zhipu_ai_api_key": ""
}
```
 - `model`: 可填 `glm-4.7、glm-4-plus、glm-4-flash、glm-4-air、glm-4-airx、glm-4-long` 等, 参考 [glm-4系列模型编码](https://bigmodel.cn/dev/api/normal-model/glm-4)
 - `zhipu_ai_api_key`: 智谱AI平台的 API KEY，在 [控制台](https://www.bigmodel.cn/usercenter/proj-mgmt/apikeys) 创建

方式二：OpenAI兼容方式接入，配置如下：
```json
{
  "bot_type": "chatGPT",
  "model": "glm-4.7",
  "open_ai_api_base": "https://open.bigmodel.cn/api/paas/v4",
  "open_ai_api_key": ""
}
```
- `bot_type`: OpenAI兼容方式
- `model`: 可填 `glm-4.7、glm-4.6、glm-4-plus、glm-4-flash、glm-4-air、glm-4-airx、glm-4-long` 等
- `open_ai_api_base`: 智谱AI平台的 BASE URL
- `open_ai_api_key`: 智谱AI平台的 API KEY
</details>

<details>
<summary>通义千问 (Qwen)</summary>

方式一：官方SDK接入，配置如下(推荐)：

```json
{
    "model": "qwen3-max",
    "dashscope_api_key": "sk-qVxxxxG"
}
```
 - `model`: 可填写 `qwen3-max、qwen-max、qwen-plus、qwen-turbo、qwen-long、qwq-plus` 等
 - `dashscope_api_key`: 通义千问的 API-KEY，参考 [官方文档](https://bailian.console.aliyun.com/?tab=api#/api) ，在 [控制台](https://bailian.console.aliyun.com/?tab=model#/api-key) 创建

方式二：OpenAI兼容方式接入，配置如下：
```json
{
  "bot_type": "chatGPT",
  "model": "qwen3-max",
  "open_ai_api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "open_ai_api_key": "sk-qVxxxxG"
}
```
- `bot_type`: OpenAI兼容方式
- `model`: 支持官方所有模型，参考[模型列表](https://help.aliyun.com/zh/model-studio/models?spm=a2c4g.11186623.0.0.78d84823Kth5on#9f8890ce29g5u)
- `open_ai_api_base`: 通义千问API的 BASE URL
- `open_ai_api_key`: 通义千问的 API-KEY
</details>

<details>
<summary>Claude</summary>

1. API Key创建：在 [Claude控制台](https://console.anthropic.com/settings/keys) 创建API Key

2. 填写配置

```json
{
    "model": "claude-sonnet-4-5",
    "claude_api_key": "YOUR_API_KEY"
}
```
 - `model`: 参考 [官方模型ID](https://docs.anthropic.com/en/docs/about-claude/models/overview#model-aliases) ，支持 `claude-opus-4-6、claude-sonnet-4-5、claude-sonnet-4-0、claude-opus-4-0、claude-3-5-sonnet-latest` 等
</details>

<details>
<summary>Gemini</summary>

API Key创建：在 [控制台](https://aistudio.google.com/app/apikey?hl=zh-cn) 创建API Key ，配置如下
```json
{
    "model": "gemini-3-flash-preview",
    "gemini_api_key": ""
}
```
 - `model`: 参考[官方文档-模型列表](https://ai.google.dev/gemini-api/docs/models?hl=zh-cn)，支持 `gemini-3-flash-preview、gemini-3-pro-preview、gemini-2.5-pro、gemini-2.0-flash` 等
</details>

<details>
<summary>DeepSeek</summary>

1. API Key创建：在 [DeepSeek平台](https://platform.deepseek.com/api_keys) 创建API Key 

2. 填写配置

```json
{
    "model": "deepseek-chat",
    "open_ai_api_key": "sk-xxxxxxxxxxx",
    "open_ai_api_base": "https://api.deepseek.com/v1", 
    "bot_type": "chatGPT"

}
```

 - `bot_type`: OpenAI兼容方式
 - `model`: 可填 `deepseek-chat、deepseek-reasoner`，分别对应的是 DeepSeek-V3 和 DeepSeek-R1 模型
 - `open_ai_api_key`: DeepSeek平台的 API Key
 - `open_ai_api_base`: DeepSeek平台 BASE URL
</details>

<details>
<summary>Kimi (Moonshot)</summary>

方式一：官方接入，配置如下：

```json
{
    "model": "moonshot-v1-128k",
    "moonshot_api_key": ""
}
```
 - `model`: 可填写 `moonshot-v1-8k、moonshot-v1-32k、moonshot-v1-128k`
 - `moonshot_api_key`: Moonshot的API-KEY，在 [控制台](https://platform.moonshot.cn/console/api-keys) 创建
 
方式二：OpenAI兼容方式接入，配置如下：
```json
{
  "bot_type": "chatGPT",
  "model": "moonshot-v1-128k",
  "open_ai_api_base": "https://api.moonshot.cn/v1",
  "open_ai_api_key": ""
}
```
- `bot_type`: OpenAI兼容方式
- `model`: 可填写 `moonshot-v1-8k、moonshot-v1-32k、moonshot-v1-128k`
- `open_ai_api_base`: Moonshot的 BASE URL
- `open_ai_api_key`: Moonshot的 API-KEY
</details>

<details>
<summary>Azure</summary>

1. API Key创建：在 [Azure平台](https://oai.azure.com/) 创建API Key 

2. 填写配置

```json
{
  "model": "",
  "use_azure_chatgpt": true,
  "open_ai_api_key": "",
  "open_ai_api_base": "",
  "azure_deployment_id": "",
  "azure_api_version": "2025-01-01-preview"
}
```

 - `model`: 留空即可
 - `use_azure_chatgpt`: 设为 true 
 - `open_ai_api_key`: Azure平台的密钥
 - `open_ai_api_base`: Azure平台的 BASE URL
 - `azure_deployment_id`: Azure平台部署的模型名称
 - `azure_api_version`: api版本以及以上参数可以在部署的 [模型配置](https://oai.azure.com/resource/deployments) 界面查看
</details>

<details>
<summary>百度文心</summary>
方式一：官方SDK接入，配置如下：

```json
{
    "model": "wenxin-4", 
    "baidu_wenxin_api_key": "IajztZ0bDxgnP9bEykU7lBer",
    "baidu_wenxin_secret_key": "EDPZn6L24uAS9d8RWFfotK47dPvkjD6G"
}
```
 - `model`: 可填 `wenxin`和`wenxin-4`，对应模型为 文心-3.5 和 文心-4.0
 - `baidu_wenxin_api_key`：参考 [千帆平台-access_token鉴权](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/dlv4pct3s) 文档获取 API Key
 - `baidu_wenxin_secret_key`：参考 [千帆平台-access_token鉴权](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/dlv4pct3s) 文档获取 Secret Key

方式二：OpenAI兼容方式接入，配置如下：
```json
{
  "bot_type": "chatGPT",
  "model": "ERNIE-4.0-Turbo-8K",
  "open_ai_api_base": "https://qianfan.baidubce.com/v2",
  "open_ai_api_key": "bce-v3/ALTxxxxxxd2b"
}
```
- `bot_type`: OpenAI兼容方式
- `model`: 支持官方所有模型，参考[模型列表](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Wm9cvy6rl)
- `open_ai_api_base`: 百度文心API的 BASE URL
- `open_ai_api_key`: 百度文心的 API-KEY，参考 [官方文档](https://cloud.baidu.com/doc/qianfan-api/s/ym9chdsy5) ，在 [控制台](https://console.bce.baidu.com/iam/#/iam/apikey/list) 创建API Key

</details>

<details>
<summary>讯飞星火</summary>

方式一：官方接入，配置如下：
参考 [官方文档-快速指引](https://www.xfyun.cn/doc/platform/quickguide.html#%E7%AC%AC%E4%BA%8C%E6%AD%A5-%E5%88%9B%E5%BB%BA%E6%82%A8%E7%9A%84%E7%AC%AC%E4%B8%80%E4%B8%AA%E5%BA%94%E7%94%A8-%E5%BC%80%E5%A7%8B%E4%BD%BF%E7%94%A8%E6%9C%8D%E5%8A%A1) 获取 `APPID、 APISecret、 APIKey` 三个参数

```json
{
  "model": "xunfei",
  "xunfei_app_id": "",
  "xunfei_api_key": "",
  "xunfei_api_secret": "",
  "xunfei_domain": "4.0Ultra",
  "xunfei_spark_url": "wss://spark-api.xf-yun.com/v4.0/chat"
}
```
 - `model`: 填 `xunfei`
 - `xunfei_domain`: 可填写 `4.0Ultra、generalv3.5、max-32k、generalv3、pro-128k、lite`
 - `xunfei_spark_url`: 填写参考 [官方文档-请求地址](https://www.xfyun.cn/doc/spark/Web.html#_1-1-%E8%AF%B7%E6%B1%82%E5%9C%B0%E5%9D%80) 的说明
 
方式二：OpenAI兼容方式接入，配置如下：
```json
{
  "bot_type": "chatGPT",
  "model": "4.0Ultra",
  "open_ai_api_base": "https://spark-api-open.xf-yun.com/v1",
  "open_ai_api_key": ""
}
```
- `bot_type`: OpenAI兼容方式
- `model`: 可填写 `4.0Ultra、generalv3.5、max-32k、generalv3、pro-128k、lite`
- `open_ai_api_base`: 讯飞星火平台的 BASE URL
- `open_ai_api_key`: 讯飞星火平台的[APIPassword](https://console.xfyun.cn/services/bm3) ，因模型而已
</details>

<details>
<summary>ModelScope</summary>

```json
{
  "bot_type": "modelscope",
  "model": "Qwen/QwQ-32B",
  "modelscope_api_key": "your_api_key",
  "modelscope_base_url": "https://api-inference.modelscope.cn/v1/chat/completions",
  "text_to_image": "MusePublic/489_ckpt_FLUX_1"
}
```

- `bot_type`: modelscope接口格式
- `model`: 参考[模型列表](https://www.modelscope.cn/models?filter=inference_type&page=1)
- `modelscope_api_key`: 参考 [官方文档-访问令牌](https://modelscope.cn/docs/accounts/token) ，在 [控制台](https://modelscope.cn/my/myaccesstoken) 
- `modelscope_base_url`: modelscope平台的 BASE URL
- `text_to_image`: 图像生成模型，参考[模型列表](https://www.modelscope.cn/models?filter=inference_type&page=1)
</details>


## 通道说明

以下对可接入通道的配置方式进行说明，应用通道代码在项目的 `channel/` 目录下。

<details>
<summary>1. Web</summary>

项目启动后默认运行Web通道，配置如下：

```json
{
    "channel_type": "web",
    "web_port": 9899
}
```

- `web_port`: 默认为 9899，可按需更改，需要服务器防火墙和安全组放行该端口
- 如本地运行，启动后请访问 `http://localhost:9899/chat` ；如服务器运行，请访问 `http://ip:9899/chat` 
> 注：请将上述 url 中的 ip 或者 port 替换为实际的值
</details>

<details>
<summary>2. Feishu - 飞书</summary>

飞书支持两种事件接收模式：WebSocket 长连接（推荐）和 Webhook。

**方式一：WebSocket 模式（推荐，无需公网 IP）**

```json
{
    "channel_type": "feishu",
    "feishu_app_id": "APP_ID",
    "feishu_app_secret": "APP_SECRET",
    "feishu_event_mode": "websocket"
}
```

**方式二：Webhook 模式（需要公网 IP）**

```json
{
    "channel_type": "feishu",
    "feishu_app_id": "APP_ID",
    "feishu_app_secret": "APP_SECRET",
    "feishu_token": "VERIFICATION_TOKEN",
    "feishu_event_mode": "webhook",
    "feishu_port": 9891
}
```

- `feishu_event_mode`: 事件接收模式，`websocket`（推荐）或 `webhook`
- WebSocket 模式需安装依赖：`pip3 install lark-oapi`

详细步骤和参数说明参考 [飞书接入](https://docs.link-ai.tech/cow/multi-platform/feishu)

</details>

<details>
<summary>3. DingTalk - 钉钉</summary>

钉钉需要在开放平台创建智能机器人应用，将以下配置填入 `config.json`：

```json
{
    "channel_type": "dingtalk",
    "dingtalk_client_id": "CLIENT_ID",
    "dingtalk_client_secret": "CLIENT_SECRET"
}
```
详细步骤和参数说明参考 [钉钉接入](https://docs.link-ai.tech/cow/multi-platform/dingtalk)
</details>

<details>
<summary>4. WeCom App - 企业微信应用</summary>

企业微信自建应用接入需在后台创建应用并启用消息回调，配置示例：

```json
{
    "channel_type": "wechatcom_app",
    "wechatcom_corp_id": "CORPID",
    "wechatcomapp_token": "TOKEN",
    "wechatcomapp_port": 9898,
    "wechatcomapp_secret": "SECRET",
    "wechatcomapp_agent_id": "AGENTID",
    "wechatcomapp_aes_key": "AESKEY"
}
```
详细步骤和参数说明参考 [企微自建应用接入](https://docs.link-ai.tech/cow/multi-platform/wechat-com)

</details>

<details>
<summary>5. WeChat MP - 微信公众号</summary>

本项目支持订阅号和服务号两种公众号，通过服务号（`wechatmp_service`）体验更佳。

**个人订阅号（wechatmp）**

```json
{
    "channel_type": "wechatmp",
    "wechatmp_token": "TOKEN",
    "wechatmp_port": 80,
    "wechatmp_app_id": "APPID",
    "wechatmp_app_secret": "APPSECRET",
    "wechatmp_aes_key": ""
}
```

**企业服务号（wechatmp_service）**

```json
{
    "channel_type": "wechatmp_service",
    "wechatmp_token": "TOKEN",
    "wechatmp_port": 80,
    "wechatmp_app_id": "APPID",
    "wechatmp_app_secret": "APPSECRET",
    "wechatmp_aes_key": ""
}
```

详细步骤和参数说明参考 [微信公众号接入](https://docs.link-ai.tech/cow/multi-platform/wechat-mp)

</details>

<details>
<summary>6. Terminal - 终端</summary>

修改 `config.json` 中的 `channel_type` 字段：

```json
{
    "channel_type": "terminal"
}
```

运行后可在终端与机器人进行对话。

</details>

<br/>

# 🔗 相关项目

- [bot-on-anything](https://github.com/zhayujie/bot-on-anything)：轻量和高可扩展的大模型应用框架，支持接入Slack, Telegram, Discord, Gmail等海外平台，可作为本项目的补充使用。
- [AgentMesh](https://github.com/MinimalFuture/AgentMesh)：开源的多智能体(Multi-Agent)框架，可以通过多智能体团队的协同来解决复杂问题。本项目基于该框架实现了[Agent插件](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/plugins/agent/README.md)，可访问终端、浏览器、文件系统、搜索引擎 等各类工具，并实现了多智能体协同。



# 🔎 常见问题

FAQs： <https://github.com/zhayujie/chatgpt-on-wechat/wiki/FAQs>

或直接在线咨询 [项目小助手](https://link-ai.tech/app/Kv2fXJcH)  (知识库持续完善中，回复供参考)

# 🛠️ 开发

欢迎接入更多应用通道，参考 [飞书通道](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/channel/feishu/feishu_channel.py) 新增自定义通道，实现接收和发送消息逻辑即可完成接入。 同时欢迎贡献新的Skills，参考 [Skill创造器说明](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/skills/skill-creator/SKILL.md)。

# ✉ 联系

欢迎提交PR、Issues进行反馈，以及通过 🌟Star 支持并关注项目更新。项目运行遇到问题可以查看 [常见问题列表](https://github.com/zhayujie/chatgpt-on-wechat/wiki/FAQs) ，以及前往 [Issues](https://github.com/zhayujie/chatgpt-on-wechat/issues) 中搜索。个人开发者可加入开源交流群参与更多讨论，企业用户可联系[产品客服](https://cdn.link-ai.tech/portal/linkai-customer-service.png)咨询。

# 🌟 贡献者

![cow contributors](https://contrib.rocks/image?repo=zhayujie/chatgpt-on-wechat&max=1000)
