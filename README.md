# 简介

> ChatGPT近期以强大的对话和信息整合能力风靡全网，可以写代码、改论文、讲故事，几乎无所不能，这让人不禁有个大胆的想法，能否用他的对话模型把我们的微信打造成一个智能机器人，可以在与好友对话中给出意想不到的回应，而且再也不用担心女朋友影响我们 ~~打游戏~~ 工作了。

最新版本支持的功能如下：

- [x] **多端部署：** 有多种部署方式可选择且功能完备，目前已支持个人微信、微信公众号和、业微信、飞书等部署方式
- [x] **基础对话：** 私聊及群聊的消息智能回复，支持多轮会话上下文记忆，支持 GPT-3.5, GPT-4, claude, 文心一言, 讯飞星火
- [x] **语音能力：** 可识别语音消息，通过文字或语音回复，支持 azure, baidu, google, openai(whisper/tts) 等多种语音模型
- [x] **图像能力：** 支持图片生成、图片识别、图生图（如照片修复），可选择 Dall-E-3, stable diffusion, replicate, midjourney, vision模型
- [x] **丰富插件：** 支持个性化插件扩展，已实现多角色切换、文字冒险、敏感词过滤、聊天记录总结、文档总结和对话等插件
- [X] **Tool工具：** 与操作系统和互联网交互，支持最新信息搜索、数学计算、天气和资讯查询、网页总结，基于 [chatgpt-tool-hub](https://github.com/goldfishh/chatgpt-tool-hub) 实现
- [x] **知识库：** 通过上传知识库文件自定义专属机器人，可作为数字分身、领域知识库、智能客服使用，基于 [LinkAI](https://link-ai.tech/console) 实现

> 欢迎接入更多应用，参考 [Terminal代码](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/channel/terminal/terminal_channel.py)实现接收和发送消息逻辑即可接入。 同时欢迎增加新的插件，参考 [插件说明文档](https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins)。

# 演示

https://github.com/zhayujie/chatgpt-on-wechat/assets/26161723/d5154020-36e3-41db-8706-40ce9f3f1b1e

Demo made by [Visionn](https://www.wangpc.cc/)

# 交流群

添加小助手微信进群，请备注 "wechat"：

<img width="240" src="./docs/images/contact.jpg">

# 更新日志

>**2023.11.10：** [1.5.2版本](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.5.2)，新增飞书通道、图像识别对话、黑名单配置

>**2023.11.10：** [1.5.0版本](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.5.0)，新增 `gpt-4-turbo`, `dall-e-3`, `tts` 模型接入，完善图像理解&生成、语音识别&生成的多模态能力

>**2023.10.16：** 支持通过意图识别使用LinkAI联网搜索、数学计算、网页访问等插件，参考[插件文档](https://docs.link-ai.tech/platform/plugins)

>**2023.09.26：** 插件增加 文件/文章链接 一键总结和对话的功能，使用参考：[插件说明](https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins/linkai#3%E6%96%87%E6%A1%A3%E6%80%BB%E7%BB%93%E5%AF%B9%E8%AF%9D%E5%8A%9F%E8%83%BD)

>**2023.08.08：** 接入百度文心一言模型，通过 [插件](https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins/linkai) 支持 Midjourney 绘图

>**2023.06.12：** 接入 [LinkAI](https://link-ai.tech/console) 平台，可在线创建领域知识库，并接入微信、公众号及企业微信中，打造专属客服机器人。使用参考 [接入文档](https://link-ai.tech/platform/link-app/wechat)。

>**2023.04.26：** 支持企业微信应用号部署，兼容插件，并支持语音图片交互，私人助理理想选择，[使用文档](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/channel/wechatcom/README.md)。(contributed by [@lanvent](https://github.com/lanvent) in [#944](https://github.com/zhayujie/chatgpt-on-wechat/pull/944))

>**2023.04.05：** 支持微信公众号部署，兼容插件，并支持语音图片交互，[使用文档](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/channel/wechatmp/README.md)。(contributed by [@JS00000](https://github.com/JS00000) in [#686](https://github.com/zhayujie/chatgpt-on-wechat/pull/686))

>**2023.04.05：** 增加能让ChatGPT使用工具的`tool`插件，[使用文档](https://github.com/goldfishh/chatgpt-on-wechat/blob/master/plugins/tool/README.md)。工具相关issue可反馈至[chatgpt-tool-hub](https://github.com/goldfishh/chatgpt-tool-hub)。(contributed by [@goldfishh](https://github.com/goldfishh) in [#663](https://github.com/zhayujie/chatgpt-on-wechat/pull/663))

>**2023.03.25：** 支持插件化开发，目前已实现 多角色切换、文字冒险游戏、管理员指令、Stable Diffusion等插件，使用参考 [#578](https://github.com/zhayujie/chatgpt-on-wechat/issues/578)。(contributed by [@lanvent](https://github.com/lanvent) in [#565](https://github.com/zhayujie/chatgpt-on-wechat/pull/565))

>**2023.03.09：** 基于 `whisper API`(后续已接入更多的语音`API`服务) 实现对微信语音消息的解析和回复，添加配置项 `"speech_recognition":true` 即可启用，使用参考 [#415](https://github.com/zhayujie/chatgpt-on-wechat/issues/415)。(contributed by [wanggang1987](https://github.com/wanggang1987) in [#385](https://github.com/zhayujie/chatgpt-on-wechat/pull/385))

>**2023.02.09：** 扫码登录存在账号限制风险，请谨慎使用，参考[#58](https://github.com/AutumnWhj/ChatGPT-wechat-bot/issues/158)

# 快速开始

快速开始文档：[项目搭建文档](https://docs.link-ai.tech/cow/quick-start)

## 准备

### 1. 账号注册

项目默认使用OpenAI接口，需前往 [OpenAI注册页面](https://beta.openai.com/signup) 创建账号，创建完账号则前往 [API管理页面](https://beta.openai.com/account/api-keys) 创建一个 API Key 并保存下来，后面需要在项目中配置这个key。接口需要海外网络访问及绑定信用卡支付。

> 默认对话模型是 openai 的 gpt-3.5-turbo，计费方式是约每 1000tokens (约750个英文单词 或 500汉字，包含请求和回复) 消耗 $0.002，图片生成是Dell E模型，每张消耗 $0.016。

项目同时也支持使用 LinkAI 接口，无需代理，可使用 文心、讯飞、GPT-3、GPT-4 等模型，支持 定制化知识库、联网搜索、MJ绘图、文档总结和对话等能力。修改配置即可一键切换，参考 [接入文档](https://link-ai.tech/platform/link-app/wechat)。

### 2.运行环境

支持 Linux、MacOS、Windows 系统（可在Linux服务器上长期运行)，同时需安装 `Python`。
> 建议Python版本在 3.7.1~3.9.X 之间，推荐3.8版本，3.10及以上版本在 MacOS 可用，其他系统上不确定能否正常运行。

> 注意：Docker 或 Railway 部署无需安装python环境和下载源码，可直接快进到下一节。

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
  "model": "gpt-3.5-turbo",                                   # 模型名称, 支持 gpt-3.5-turbo, gpt-3.5-turbo-16k, gpt-4, wenxin, xunfei
  "proxy": "",                                                # 代理客户端的ip和端口，国内环境开启代理的需要填写该项，如 "127.0.0.1:7890"
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
  "azure_deployment_id": "",                                  # 采用Azure ChatGPT时，模型部署名称
  "azure_api_version": "",                                    # 采用Azure ChatGPT时，API版本
  "character_desc": "你是ChatGPT, 一个由OpenAI训练的大型语言模型, 你旨在回答并解决人们的任何问题，并且可以使用多种语言与人交流。",  # 人格描述
  # 订阅消息，公众号和企业微信channel中请填写，当被订阅时会自动回复，可使用特殊占位符。目前支持的占位符有{trigger_prefix}，在程序中它会自动替换成bot的触发词。
  "subscribe_msg": "感谢您的关注！\n这里是ChatGPT，可以自由对话。\n支持语音对话。\n支持图片输出，画字开头的消息将按要求创作图片。\n支持角色扮演和文字冒险等丰富插件。\n输入{trigger_prefix}#help 查看详细指令。",
  "use_linkai": false,                                        # 是否使用LinkAI接口，默认关闭，开启后可国内访问，使用知识库和MJ
  "linkai_api_key": "",                                       # LinkAI Api Key
  "linkai_app_code": ""                                       # LinkAI 应用code
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

+ `model`: 模型名称，目前支持 `gpt-3.5-turbo`, `text-davinci-003`, `gpt-4`, `gpt-4-32k`, `wenxin` , `claude` ,  `xunfei`(其中gpt-4 api暂未完全开放，申请通过后可使用)
+ `temperature`,`frequency_penalty`,`presence_penalty`: Chat API接口参数，详情参考[OpenAI官方文档。](https://platform.openai.com/docs/api-reference/chat)
+ `proxy`：由于目前 `openai` 接口国内无法访问，需配置代理客户端的地址，详情参考  [#351](https://github.com/zhayujie/chatgpt-on-wechat/issues/351)
+ 对于图像生成，在满足个人或群组触发条件外，还需要额外的关键词前缀来触发，对应配置 `image_create_prefix `
+ 关于OpenAI对话及图片接口的参数配置（内容自由度、回复字数限制、图片大小等），可以参考 [对话接口](https://beta.openai.com/docs/api-reference/completions) 和 [图像接口](https://beta.openai.com/docs/api-reference/completions)  文档，在[`config.py`](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/config.py)中检查哪些参数在本项目中是可配置的。
+ `conversation_max_tokens`：表示能够记忆的上下文最大字数（一问一答为一组对话，如果累积的对话字数超出限制，就会优先移除最早的一组对话）
+ `rate_limit_chatgpt`，`rate_limit_dalle`：每分钟最高问答速率、画图速率，超速后排队按序处理。
+ `clear_memory_commands`: 对话内指令，主动清空前文记忆，字符串数组可自定义指令别名。
+ `hot_reload`: 程序退出后，暂存微信扫码状态，默认关闭。
+ `character_desc` 配置中保存着你对机器人说的一段话，他会记住这段话并作为他的设定，你可以为他定制任何人格      (关于会话上下文的更多内容参考该 [issue](https://github.com/zhayujie/chatgpt-on-wechat/issues/43))
+ `subscribe_msg`：订阅消息，公众号和企业微信channel中请填写，当被订阅时会自动回复， 可使用特殊占位符。目前支持的占位符有{trigger_prefix}，在程序中它会自动替换成bot的触发词。

**5.LinkAI配置 (可选)**

+ `use_linkai`: 是否使用LinkAI接口，开启后可国内访问，使用知识库和 `Midjourney` 绘画, 参考 [文档](https://link-ai.tech/platform/link-app/wechat)
+ `linkai_api_key`: LinkAI Api Key，可在 [控制台](https://link-ai.tech/console/interface) 创建
+ `linkai_app_code`: LinkAI 应用code，选填

**本说明文档可能会未及时更新，当前所有可选的配置项均在该[`config.py`](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/config.py)中列出。**

## 运行

### 1.本地运行

如果是开发机 **本地运行**，直接在项目根目录下执行：

```bash
python3 app.py                                    # windows环境下该命令通常为 python app.py
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

> 使用docker部署无需下载源码和安装依赖，只需要获取 docker-compose.yml 配置文件并启动容器即可。

> 前提是需要安装好 `docker` 及 `docker-compose`，安装成功的表现是执行 `docker -v` 和 `docker-compose version` (或 docker compose version) 可以查看到版本号，可前往 [docker官网](https://docs.docker.com/engine/install/) 进行下载。

#### (1) 下载 docker-compose.yml 文件

```bash
wget https://open-1317903499.cos.ap-guangzhou.myqcloud.com/docker-compose.yml
```

下载完成后打开 `docker-compose.yml` 修改所需配置，如 `OPEN_AI_API_KEY` 和 `GROUP_NAME_WHITE_LIST` 等。

#### (2) 启动容器

在 `docker-compose.yml` 所在目录下执行以下命令启动容器：

```bash
sudo docker compose up -d
```

运行 `sudo docker ps` 能查看到 NAMES 为 chatgpt-on-wechat 的容器即表示运行成功。

注意：

 - 如果 `docker-compose` 是 1.X 版本 则需要执行 `sudo  docker-compose up -d` 来启动容器
 - 该命令会自动去 [docker hub](https://hub.docker.com/r/zhayujie/chatgpt-on-wechat) 拉取 latest 版本的镜像，latest 镜像会在每次项目 release 新的版本时生成

最后运行以下命令可查看容器运行日志，扫描日志中的二维码即可完成登录：

```bash
sudo docker logs -f chatgpt-on-wechat
```

#### (3) 插件使用

如果需要在docker容器中修改插件配置，可通过挂载的方式完成，将 [插件配置文件](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/plugins/config.json.template)
重命名为 `config.json`，放置于 `docker-compose.yml` 相同目录下，并在 `docker-compose.yml` 中的 `chatgpt-on-wechat` 部分下添加 `volumes` 映射:

```
volumes:
  - ./config.json:/app/plugins/config.json
```

### 4. Railway部署

> Railway 每月提供5刀和最多500小时的免费额度。 (07.11更新: 目前大部分账号已无法免费部署)

1. 进入 [Railway](https://railway.app/template/qApznZ?referralCode=RC3znh)
2. 点击 `Deploy Now` 按钮。
3. 设置环境变量来重载程序运行的参数，例如`open_ai_api_key`, `character_desc`。

**一键部署:**
  
  [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/qApznZ?referralCode=RC3znh)

## 常见问题

FAQs： <https://github.com/zhayujie/chatgpt-on-wechat/wiki/FAQs>

或直接在线咨询 [项目小助手](https://link-ai.tech/app/Kv2fXJcH)  (beta版本，语料完善中，回复仅供参考)

## 联系

欢迎提交PR、Issues，以及Star支持一下。程序运行遇到问题可以查看 [常见问题列表](https://github.com/zhayujie/chatgpt-on-wechat/wiki/FAQs) ，其次前往 [Issues](https://github.com/zhayujie/chatgpt-on-wechat/issues) 中搜索。参与更多讨论可加入技术交流群。
