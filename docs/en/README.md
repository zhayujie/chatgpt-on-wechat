<p align="center"><img src="https://github.com/user-attachments/assets/eca9a9ec-8534-4615-9e0f-96c5ac1d10a3" alt="CowAgent" width="550" /></p>

<p align="center">
  <a href="https://github.com/zhayujie/chatgpt-on-wechat/releases/latest"><img src="https://img.shields.io/github/v/release/zhayujie/chatgpt-on-wechat" alt="Latest release"></a>
  <a href="https://github.com/zhayujie/chatgpt-on-wechat/blob/master/LICENSE"><img src="https://img.shields.io/github/license/zhayujie/chatgpt-on-wechat" alt="License: MIT"></a>
  <a href="https://github.com/zhayujie/chatgpt-on-wechat"><img src="https://img.shields.io/github/stars/zhayujie/chatgpt-on-wechat?style=flat-square" alt="Stars"></a> <br/>
  [<a href="https://github.com/zhayujie/chatgpt-on-wechat/blob/master/README.md">中文</a>] | [English]
</p>

**CowAgent** is an AI super assistant powered by LLMs, capable of autonomous task planning, operating computers and external resources, creating and executing Skills, and continuously growing with long-term memory. It supports flexible model switching, handles text, voice, images, and files, and can be integrated into Web, Feishu, DingTalk, WeCom, and WeChat Official Account — running 7×24 hours on your personal computer or server.

<p align="center">
  <a href="https://cowagent.ai/">🌐 Website</a> &nbsp;·&nbsp;
  <a href="https://docs.cowagent.ai/en/intro/index">📖 Docs</a> &nbsp;·&nbsp;
  <a href="https://docs.cowagent.ai/en/guide/quick-start">🚀 Quick Start</a>
</p>

## Introduction

> CowAgent is both an out-of-the-box AI super assistant and a highly extensible Agent framework. You can extend it with new model interfaces, channels, built-in tools, and the Skills system to flexibly implement various customization needs.

- ✅ **Autonomous Task Planning**: Understands complex tasks and autonomously plans execution, continuously thinking and invoking tools until goals are achieved. Supports accessing files, terminal, browser, schedulers, and other system resources via tools.
- ✅ **Long-term Memory**: Automatically persists conversation memory to local files and databases, including core memory and daily memory, with keyword and vector retrieval support.
- ✅ **Skills System**: Implements a Skills creation and execution engine with multiple built-in skills, and supports custom Skills development through natural language conversation.
- ✅ **Multimodal Messages**: Supports parsing, processing, generating, and sending text, images, voice, files, and other message types.
- ✅ **Multiple Model Support**: Supports OpenAI, Claude, Gemini, DeepSeek, MiniMax, GLM, Qwen, Kimi, Doubao, and other mainstream model providers.
- ✅ **Multi-platform Deployment**: Runs on local computers or servers, integrable into Web, Feishu, DingTalk, WeChat Official Account, and WeCom applications.
- ✅ **Knowledge Base**: Integrates enterprise knowledge base capabilities via the [LinkAI](https://link-ai.tech) platform.

## Disclaimer

1. This project follows the [MIT License](/LICENSE) and is intended for technical research and learning. Users must comply with local laws, regulations, policies, and corporate bylaws. Any illegal or rights-infringing use is prohibited.
2. Agent mode consumes more tokens than normal chat mode. Choose models based on effectiveness and cost. Agent has access to the host OS — please deploy in trusted environments.
3. CowAgent focuses on open-source development and does not participate in, authorize, or issue any cryptocurrency.

## Changelog

> **2026.02.03:** [v2.0.0](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/2.0.0) — Full upgrade to AI super assistant with multi-step task planning, long-term memory, built-in tools, Skills framework, new models, and optimized channels.

> **2025.05.23:** [v1.7.6](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.7.6) — Web channel optimization, AgentMesh multi-agent plugin, Baidu TTS, claude-4-sonnet/opus support.

> **2025.04.11:** [v1.7.5](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.7.5) — wechatferry protocol, DeepSeek model, Tencent Cloud voice, ModelScope and Gitee-AI support.

> **2024.12.13:** [v1.7.4](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.7.4) — Gemini 2.0 model, Web channel, memory leak fix.

Full changelog: [Release Notes](https://docs.cowagent.ai/en/releases/overview)

<br/>

## 🚀 Quick Start

The project provides a one-click script for installation, configuration, startup, and management:

```bash
bash <(curl -sS https://cdn.link-ai.tech/code/cow/run.sh)
```

After running, the Web service starts by default. Access `http://localhost:9899/chat` to chat.

Script usage: [One-click Install](https://docs.cowagent.ai/en/guide/quick-start)

### Manual Installation

**1. Clone the project**

```bash
git clone https://github.com/zhayujie/chatgpt-on-wechat
cd chatgpt-on-wechat/
```

**2. Install dependencies**

```bash
pip3 install -r requirements.txt
pip3 install -r requirements-optional.txt   # optional but recommended
```

**3. Configure**

```bash
cp config-template.json config.json
```

Fill in your model API key and channel type in `config.json`. See the [configuration docs](https://docs.cowagent.ai/en/guide/manual-install) for details.

**4. Run**

```bash
python3 app.py
```

For server background run:

```bash
nohup python3 app.py & tail -f nohup.out
```

### Docker Deployment

```bash
wget https://cdn.link-ai.tech/code/cow/docker-compose.yml
# Edit docker-compose.yml with your config
sudo docker compose up -d
sudo docker logs -f chatgpt-on-wechat
```

<br/>

## Models

Supports mainstream model providers. Recommended models for Agent mode:

| Provider | Recommended Model |
| --- | --- |
| MiniMax | `MiniMax-M2.5` |
| GLM | `glm-5` |
| Kimi | `kimi-k2.5` |
| Doubao | `doubao-seed-2-0-code-preview-260215` |
| Qwen | `qwen3.5-plus` |
| Claude | `claude-sonnet-4-6` |
| Gemini | `gemini-3.1-pro-preview` |
| OpenAI | `gpt-4.1` |
| DeepSeek | `deepseek-chat` |

For detailed configuration of each model, see the [Models documentation](https://docs.cowagent.ai/en/models/index).

<br/>

## Channels

Supports multiple platforms. Set `channel_type` in `config.json` to switch:

| Channel | `channel_type` | Docs |
| --- | --- | --- |
| Web (default) | `web` | [Web Channel](https://docs.cowagent.ai/en/channels/web) |
| Feishu | `feishu` | [Feishu Setup](https://docs.cowagent.ai/en/channels/feishu) |
| DingTalk | `dingtalk` | [DingTalk Setup](https://docs.cowagent.ai/en/channels/dingtalk) |
| WeCom App | `wechatcom_app` | [WeCom Setup](https://docs.cowagent.ai/en/channels/wecom) |
| WeChat MP | `wechatmp` / `wechatmp_service` | [WeChat MP Setup](https://docs.cowagent.ai/en/channels/wechatmp) |
| Terminal | `terminal` | — |

Multiple channels can be enabled simultaneously, separated by commas: `"channel_type": "feishu,dingtalk"`.

<br/>

## Enterprise Services

<a href="https://link-ai.tech" target="_blank"><img width="720" src="https://cdn.link-ai.tech/image/link-ai-intro.jpg"></a>

> [LinkAI](https://link-ai.tech/) is a one-stop AI agent platform for enterprises and developers, integrating multimodal LLMs, knowledge bases, Agent plugins, and workflows. Supports one-click integration with mainstream platforms, SaaS and private deployment.

<br/>

## 🔗 Related Projects

- [bot-on-anything](https://github.com/zhayujie/bot-on-anything): Lightweight and highly extensible LLM application framework supporting Slack, Telegram, Discord, Gmail, and more.
- [AgentMesh](https://github.com/MinimalFuture/AgentMesh): Open-source Multi-Agent framework for complex problem solving through agent team collaboration.

## 🔎 FAQ

FAQs: <https://github.com/zhayujie/chatgpt-on-wechat/wiki/FAQs>

## 🛠️ Contributing

Welcome to add new channels, referring to the [Feishu channel](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/channel/feishu/feishu_channel.py) as an example. Also welcome to contribute new Skills, referring to the [Skill Creator docs](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/skills/skill-creator/SKILL.md).

## ✉ Contact

Welcome to submit PRs and Issues, and support the project with a 🌟 Star. For questions, check the [FAQ list](https://github.com/zhayujie/chatgpt-on-wechat/wiki/FAQs) or search [Issues](https://github.com/zhayujie/chatgpt-on-wechat/issues).

## 🌟 Contributors

![cow contributors](https://contrib.rocks/image?repo=zhayujie/chatgpt-on-wechat&max=1000)
