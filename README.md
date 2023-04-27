# 简介

> ChatGPT近期以强大的对话和信息整合能力风靡全网，可以写代码、改论文、讲故事，几乎无所不能，这让人不禁有个大胆的想法，能否用他的对话模型把我们的微信打造成一个智能机器人，可以在与好友对话中给出意想不到的回应，而且再也不用担心女朋友影响我们 ~~打游戏~~ 工作了。

最新版本支持的功能如下：

- [x] **多端部署：** 有多种部署方式可选择且功能完备，目前已支持个人微信，微信公众号和企业微信应用等部署方式
- [x] **基础对话：** 私聊及群聊的消息智能回复，支持多轮会话上下文记忆，支持 GPT-3，GPT-3.5，GPT-4模型
- [x] **语音识别：** 可识别语音消息，通过文字或语音回复，支持 azure, baidu, google, openai等多种语音模型
- [x] **图片生成：** 支持图片生成 和 图生图（如照片修复），可选择 Dell-E, stable diffusion, replicate模型
- [x] **丰富插件：** 支持个性化插件扩展，已实现多角色切换、文字冒险、敏感词过滤、聊天记录总结等插件
- [X] **Tool工具：** 与操作系统和互联网交互，支持最新信息搜索、数学计算、天气和资讯查询、网页总结，基于 [chatgpt-tool-hub](https://github.com/goldfishh/chatgpt-tool-hub) 实现

> 欢迎接入更多应用，参考 [Terminal代码](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/channel/terminal/terminal_channel.py)实现接收和发送消息逻辑即可接入。 同时欢迎增加新的插件，参考 [插件说明文档](https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins)。

**一键部署:**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/qApznZ?referralCode=RC3znh)

# 演示

https://user-images.githubusercontent.com/26161723/233777277-e3b9928e-b88f-43e2-b0e0-3cbc923bc799.mp4

Demo made by [Visionn](https://www.wangpc.cc/)

# 更新日志

>**2023.04.26：** 支持企业微信应用号部署，兼容插件，并支持语音图片交互，支持Railway部署，[使用文档](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/channel/wechatcom/README.md)。(contributed by [@lanvent](https://github.com/lanvent) in [#944](https://github.com/zhayujie/chatgpt-on-wechat/pull/944))

>**2023.04.05：** 支持微信公众号部署，兼容插件，并支持语音图片交互，[使用文档](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/channel/wechatmp/README.md)。(contributed by [@JS00000](https://github.com/JS00000) in [#686](https://github.com/zhayujie/chatgpt-on-wechat/pull/686))

>**2023.04.05：** 增加能让ChatGPT使用工具的`tool`插件，[使用文档](https://github.com/goldfishh/chatgpt-on-wechat/blob/master/plugins/tool/README.md)。工具相关issue可反馈至[chatgpt-tool-hub](https://github.com/goldfishh/chatgpt-tool-hub)。(contributed by [@goldfishh](https://github.com/goldfishh) in [#663](https://github.com/zhayujie/chatgpt-on-wechat/pull/663))

>**2023.03.25：** 支持插件化开发，目前已实现 多角色切换、文字冒险游戏、管理员指令、Stable Diffusion等插件，使用参考 [#578](https://github.com/zhayujie/chatgpt-on-wechat/issues/578)。(contributed by [@lanvent](https://github.com/lanvent) in [#565](https://github.com/zhayujie/chatgpt-on-wechat/pull/565))

>**2023.03.09：** 基于 `whisper API`(后续已接入更多的语音`API`服务) 实现对微信语音消息的解析和回复，添加配置项 `"speech_recognition":true` 即可启用，使用参考 [#415](https://github.com/zhayujie/chatgpt-on-wechat/issues/415)。(contributed by [wanggang1987](https://github.com/wanggang1987) in [#385](https://github.com/zhayujie/chatgpt-on-wechat/pull/385))

>**2023.03.02：** 接入[ChatGPT API](https://platform.openai.com/docs/guides/chat) (gpt-3.5-turbo)，默认使用该模型进行对话，需升级openai依赖 (`pip3 install --upgrade openai`)。网络问题参考 [#351](https://github.com/zhayujie/chatgpt-on-wechat/issues/351)

>**2023.02.09：** 扫码登录存在账号限制风险，请谨慎使用，参考[#58](https://github.com/AutumnWhj/ChatGPT-wechat-bot/issues/158)

# 快速开始

## 准备

### 1. OpenAI账号注册

前往 [OpenAI注册页面](https://beta.openai.com/signup) 创建账号，参考这篇 [教程](https://www.pythonthree.com/register-openai-chatgpt/) 可以通过虚拟手机号来接收验证码。创建完账号则前往 [API管理页面](https://beta.openai.com/account/api-keys) 创建一个 API Key 并保存下来，后面需要在项目中配置这个key。

> 项目中默认使用的对话模型是 gpt3.5 turbo，计费方式是约每 500 汉字 (包含请求和回复) 消耗 $0.002，图片生成是每张消耗 $0.016。

### 2.运行环境

支持 Linux、MacOS、Windows 系统（可在Linux服务器上长期运行)，同时需安装 `Python`。
> 建议Python版本在 3.7.1~3.9.X 之间，推荐3.8版本，3.10及以上版本在 MacOS 可用，其他系统上不确定能否正常运行。

**(1) 克隆项目代码：**

```bash
git clone https://github.com/zhayujie/chatgpt-on-wechat
cd chatgpt-on-wechat/
```

**(2) 安装核心依赖 (必选)：**
> 能够使用`itchat`创建机器人，并具有文字交流功能所需的最小依赖集合。
```bash
pip3 install -r requirements.txt
```

**(3) 拓展依赖 (可选，建议安装)：**

```bash
pip3 install -r requirements-optional.txt
```
> 如果某项依赖安装失败请注释掉对应的行再继续。

其中`tiktoken`要求`python`版本在3.8以上，它用于精确计算会话使用的tokens数量，强烈建议安装。


使用`google`或`baidu`语音识别需安装`ffmpeg`，

默认的`openai`语音识别不需要安装`ffmpeg`。

参考[#415](https://github.com/zhayujie/chatgpt-on-wechat/issues/415)

使用`azure`语音功能需安装依赖，并参考[文档](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/quickstarts/setup-platform?pivots=programming-language-python&tabs=linux%2Cubuntu%2Cdotnet%2Cjre%2Cmaven%2Cnodejs%2Cmac%2Cpypi)的环境要求。
:

```bash
pip3 install azure-cognitiveservices-speech
```

## 配置

配置文件的模板在根目录的`config-template.json`中，需复制该模板创建最终生效的 `config.json` 文件：

```bash
  cp config-template.json config.json
```

然后在`config.json`中填入配置，以下是对默认配置的说明，可根据需要进行自定义修改（请去掉注释）：

```bash
# config.json文件内容示例
{
  "open_ai_api_key": "YOUR API KEY",                          # 填入上面创建的 OpenAI API KEY
  "model": "gpt-3.5-turbo",                                   # 模型名称。当use_azure_chatgpt为true时，其名称为Azure上model deployment名称
  "proxy": "127.0.0.1:7890",                                  # 代理客户端的ip和端口
  "single_chat_prefix": ["bot", "@bot"],                      # 私聊时文本需要包含该前缀才能触发机器人回复
  "single_chat_reply_prefix": "[bot] ",                       # 私聊时自动回复的前缀，用于区分真人
  "group_chat_prefix": ["@bot"],                              # 群聊时包含该前缀则会触发机器人回复
  "group_name_white_list": ["ChatGPT测试群", "ChatGPT测试群2"], # 开启自动回复的群名称列表
  "group_chat_in_one_session": ["ChatGPT测试群"],              # 支持会话上下文共享的群名称  
  "image_create_prefix": ["画", "看", "找"],                   # 开启图片回复的前缀
  "conversation_max_tokens": 1000,                            # 支持上下文记忆的最多字符数
  "speech_recognition": false,                                # 是否开启语音识别
  "group_speech_recognition": false,                          # 是否开启群组语音识别
  "use_azure_chatgpt": false,                                 # 是否使用Azure ChatGPT service代替openai ChatGPT service. 当设置为true时需要设置 open_ai_api_base，如 https://xxx.openai.azure.com/
  "character_desc": "你是ChatGPT, 一个由OpenAI训练的大型语言模型, 你旨在回答并解决人们的任何问题，并且可以使用多种语言与人交流。",  # 人格描述
  # 订阅消息，公众号和企业微信channel中请填写，当被订阅时会自动回复，可使用特殊占位符。目前支持的占位符有{trigger_prefix}，在程序中它会自动替换成bot的触发词。
  "subscribe_msg": "感谢您的关注！\n这里是ChatGPT，可以自由对话。\n支持语音对话。\n支持图片输出，画字开头的消息将按要求创作图片。\n支持角色扮演和文字冒险等丰富插件。\n输入{trigger_prefix}#help 查看详细指令。"
}
```
**配置说明：**

**1.个人聊天**

+ 个人聊天中，需要以 "bot"或"@bot" 为开头的内容触发机器人，对应配置项 `single_chat_prefix` (如果不需要以前缀触发可以填写  `"single_chat_prefix": [""]`)
+ 机器人回复的内容会以 "[bot] " 作为前缀， 以区分真人，对应的配置项为 `single_chat_reply_prefix` (如果不需要前缀可以填写 `"single_chat_reply_prefix": ""`)

**2.群组聊天**

+ 群组聊天中，群名称需配置在 `group_name_white_list ` 中才能开启群聊自动回复。如果想对所有群聊生效，可以直接填写 `"group_name_white_list": ["ALL_GROUP"]`
+ 默认只要被人 @ 就会触发机器人自动回复；另外群聊天中只要检测到以 "@bot" 开头的内容，同样会自动回复（方便自己触发），这对应配置项 `group_chat_prefix`
+ 可选配置: `group_name_keyword_white_list`配置项支持模糊匹配群名称，`group_chat_keyword`配置项则支持模糊匹配群消息内容，用法与上述两个配置项相同。（Contributed by [evolay](https://github.com/evolay))
+ `group_chat_in_one_session`：使群聊共享一个会话上下文，配置 `["ALL_GROUP"]` 则作用于所有群聊

**3.语音识别**

+ 添加 `"speech_recognition": true` 将开启语音识别，默认使用openai的whisper模型识别为文字，同时以文字回复，该参数仅支持私聊 (注意由于语音消息无法匹配前缀，一旦开启将对所有语音自动回复，支持语音触发画图)；
+ 添加 `"group_speech_recognition": true` 将开启群组语音识别，默认使用openai的whisper模型识别为文字，同时以文字回复，参数仅支持群聊 (会匹配group_chat_prefix和group_chat_keyword, 支持语音触发画图)；
+ 添加 `"voice_reply_voice": true` 将开启语音回复语音（同时作用于私聊和群聊），但是需要配置对应语音合成平台的key，由于itchat协议的限制，只能发送语音mp3文件，若使用wechaty则回复的是微信语音。

**4.其他配置**

+ `model`: 模型名称，目前支持 `gpt-3.5-turbo`, `text-davinci-003`, `gpt-4`, `gpt-4-32k`  (其中gpt-4 api暂未开放)
+ `temperature`,`frequency_penalty`,`presence_penalty`: Chat API接口参数，详情参考[OpenAI官方文档。](https://platform.openai.com/docs/api-reference/chat)
+ `proxy`：由于目前 `openai` 接口国内无法访问，需配置代理客户端的地址，详情参考  [#351](https://github.com/zhayujie/chatgpt-on-wechat/issues/351)
+ 对于图像生成，在满足个人或群组触发条件外，还需要额外的关键词前缀来触发，对应配置 `image_create_prefix `
+ 关于OpenAI对话及图片接口的参数配置（内容自由度、回复字数限制、图片大小等），可以参考 [对话接口](https://beta.openai.com/docs/api-reference/completions) 和 [图像接口](https://beta.openai.com/docs/api-reference/completions)  文档直接在 [代码](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/bot/openai/open_ai_bot.py) `bot/openai/open_ai_bot.py` 中进行调整。
+ `conversation_max_tokens`：表示能够记忆的上下文最大字数（一问一答为一组对话，如果累积的对话字数超出限制，就会优先移除最早的一组对话）
+ `rate_limit_chatgpt`，`rate_limit_dalle`：每分钟最高问答速率、画图速率，超速后排队按序处理。
+ `clear_memory_commands`: 对话内指令，主动清空前文记忆，字符串数组可自定义指令别名。
+ `hot_reload`: 程序退出后，暂存微信扫码状态，默认关闭。
+ `character_desc` 配置中保存着你对机器人说的一段话，他会记住这段话并作为他的设定，你可以为他定制任何人格      (关于会话上下文的更多内容参考该 [issue](https://github.com/zhayujie/chatgpt-on-wechat/issues/43))
+ `subscribe_msg`：订阅消息，公众号和企业微信channel中请填写，当被订阅时会自动回复， 可使用特殊占位符。目前支持的占位符有{trigger_prefix}，在程序中它会自动替换成bot的触发词。

**所有可选的配置项均在该[文件](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/config.py)中列出。**

## 运行

### 1.本地运行

如果是开发机 **本地运行**，直接在项目根目录下执行：

```bash
python3 app.py
```
终端输出二维码后，使用微信进行扫码，当输出 "Start auto replying" 时表示自动回复程序已经成功运行了（注意：用于登录的微信需要在支付处已完成实名认证）。扫码登录后你的账号就成为机器人了，可以在微信手机端通过配置的关键词触发自动回复 (任意好友发送消息给你，或是自己发消息给好友)，参考[#142](https://github.com/zhayujie/chatgpt-on-wechat/issues/142)。


### 2.服务器部署

使用nohup命令在后台运行程序：

```bash
touch nohup.out                                   # 首次运行需要新建日志文件  
nohup python3 app.py & tail -f nohup.out          # 在后台运行程序并通过日志输出二维码
```
扫码登录后程序即可运行于服务器后台，此时可通过 `ctrl+c` 关闭日志，不会影响后台程序的运行。使用 `ps -ef | grep app.py | grep -v grep` 命令可查看运行于后台的进程，如果想要重新启动程序可以先 `kill` 掉对应的进程。日志关闭后如果想要再次打开只需输入 `tail -f nohup.out`。此外，`scripts` 目录下有一键运行、关闭程序的脚本供使用。

> **多账号支持：** 将项目复制多份，分别启动程序，用不同账号扫码登录即可实现同时运行。

> **特殊指令：** 用户向机器人发送 **#reset** 即可清空该用户的上下文记忆。


### 3.Docker部署

参考文档 [Docker部署](https://github.com/limccn/chatgpt-on-wechat/wiki/Docker%E9%83%A8%E7%BD%B2)   (Contributed by [limccn](https://github.com/limccn))。

### 4. Railway部署 (✅推荐)
> Railway每月提供5刀和最多500小时的免费额度。
1. 进入 [Railway](https://railway.app/template/qApznZ?referralCode=RC3znh)。
2. 点击 `Deploy Now` 按钮。
3. 设置环境变量来重载程序运行的参数，例如`open_ai_api_key`, `character_desc`。

## 常见问题

FAQs： <https://github.com/zhayujie/chatgpt-on-wechat/wiki/FAQs>


## 联系

欢迎提交PR、Issues，以及Star支持一下。程序运行遇到问题优先查看 [常见问题列表](https://github.com/zhayujie/chatgpt-on-wechat/wiki/FAQs) ，其次前往 [Issues](https://github.com/zhayujie/chatgpt-on-wechat/issues) 中搜索。如果你想了解更多项目细节，并与开发者们交流更多关于AI技术的实践，欢迎加入星球:

<a href="https://public.zsxq.com/groups/88885848842852.html"><img width="360" src="./docs/images/planet.jpg"></a>
