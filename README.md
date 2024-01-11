# 简介

> 使用微软Bing搭建微信聊天机器人，支持个人微信、公众号、企业微信部署，能处理文本、docx,pdf,word文件和图片，处理微信链接的分享，访问互联网，支持预设prompt injection定制专属智能助理。
最新版本支持的功能如下：

- [x] **多端部署：** 有多种部署方式可选择且功能完备，目前已支持个人微信、微信公众号和、企业微信、飞书等部署方式
- [x] **基础对话：** 私聊及群聊的消息智能回复，支持多轮会话上下文记忆
- [x] **图像能力：** 支持图片识别、图生图如照片修复(插件)
- [x] **丰富插件：** 支持个性化插件扩展，已实现多角色切换、文字冒险、敏感词过滤、聊天记录总结、文档总结和对话等插件
- [X] **Tool工具：** 与互联网交互，支持最新信息搜索、数学计算、天气和资讯查询、网页总结。
- [x] **Prompt Injection：** 绕过微软BING的自我审查来自定义专属机器人，可作为数字分身、智能客服使用

> 欢迎接入更多应用，参考 [Terminal代码](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/channel/terminal/terminal_channel.py)实现接收和发送消息逻辑即可接入。 同时欢迎增加新的插件，参考 [插件说明文档](https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins)。


# Knowing issues

> when uploading a local storage image, server will response unexpected error with json data, which indicates unstable performance of image recognition, so it's a server exception.

# Planned updates

> 向聊天中发送“内容正在生成中”， 如果当前生成内容的时间超过了30s。

> let's see if the tip message from bot will pollute the conversation.

> ~~when one reply is in processing user can stop the generation of content immediately by sending a message, and the stopped reply won't be stored in the chat history~~


# 演示



# 交流群



# Update logs

>**2023.11.11：** when one reply is in processing user can stop the generation of content immediately by sending a message, and the stopped reply won't be stored in the chat history.

# 快速开始

## 准备

### 1. Bing cookies 获取

前往 [Bing对话页面](https://www.bing.com/search?q=Bing+AI&showconv=1&FORM=hpcodx)开始一段对话。收到回复后则前往浏览器扩展商店中安装[Cookies Editor](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) 回到之前的聊天页面export json并复制下来，后面在项目的主文件夹中添加cookies.json文件并把复制的内容粘贴上去保存。

> 项目中默认使用的Bing对话模式是creative，使用这种方式免费，快速，方便不需要消耗Api key。

### 2.运行环境

支持 Linux、MacOS、Windows 系统（可在Linux服务器上长期运行)，同时需安装 `Python`。
> 建议Python版本在 3.7.1~3.9.X 之间，推荐3.8版本，3.10及以上版本在 MacOS 可用，其他系统上不确定能否正常运行。

> 注意：Docker 或 Railway 部署无需安装python环境和下载源码，可直接快进到下一节。

**(1) 克隆项目代码：**

```bash
git clone https://github.com/JayGarland/chatgpt-on-wechat.git
cd chatgpt-on-wechat/
```

**(2) 安装核心依赖 (必选)：**
> 能够使用`itchat`创建机器人，并具有文字交流功能所需的最小依赖集合。
```bash
pip3 install -r requirements.txt
```

## 配置

配置文件在根目录的`config.json`中：

在`config.json`中填入配置，以下是对默认配置的说明，可根据需要进行自定义修改（请去掉注释）(since we used the model of sydney so we don't need to modify or add any info in config json about chatgpt or any other else)：

```bash
# config.json文件内容示例
{
  "open_ai_api_key": "YOUR API KEY",                          # 填入上面创建的 OpenAI API KEY
  "model": "sydney",                                   # 模型名称, 支持 gpt-3.5-turbo, gpt-3.5-turbo-16k, gpt-4, wenxin, xunfei
  "proxy": "",                                                # 代理客户端的ip和端口，国内环境开启代理的需要填写该项，如 "127.0.0.1:7890"
  "single_chat_prefix": [""],                      # 私聊时文本需要包含该前缀才能触发机器人回复
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
  "character_desc": "",  
  # 订阅消息，公众号和企业微信channel中请填写，当被订阅时会自动回复，可使用特殊占位符。目前支持的占位符有{trigger_prefix}，在程序中它会自动替换成bot的触发词。
  "subscribe_msg": "",
  "use_linkai": false,                                        # 是否使用LinkAI接口，默认关闭，开启后可国内访问，使用知识库和MJ
  "linkai_api_key": "",                                       # LinkAI Api Key
  "linkai_app_code": ""                                       # LinkAI 应用code
}

```
**配置说明：**

**个人聊天**

+ 个人聊天中，发送消息即可触发机器人，对应配置项 `single_chat_prefix` (如果不需要以前缀触发可以填写  `"single_chat_prefix": [""]`)
+ 机器人回复的内容会以 "[bot] " 作为前缀， 以区分真人，对应的配置项为 `single_chat_reply_prefix` (如果不需要前缀可以填写 `"single_chat_reply_prefix": ""`)



**4.其他配置**

+ `model`: 模型名称，填 `sydney`
+ `proxy`：由于目前 `bing` 接口国内无法访问，需配置代理客户端的地址，详情参考  [#351](https://github.com/zhayujie/chatgpt-on-wechat/issues/351)
+ 对于图像生成，在满足个人或群组触发条件外，格式是需要用户发送图片后再对智能助理发消息即可触发
+ `clear_memory_commands`: 对话内指令，主动清空前文记忆，字符串数组可自定义指令别名。
+ `hot_reload`: 程序退出后，暂存微信扫码状态，默认关闭。


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

FAQs： <https://github.com/JayGarland/chatgpt-on-wechat/wiki/FAQs>

## 联系

欢迎提交PR、Issues，以及Star支持一下。程序运行遇到问题可以查看 [常见问题列表](https://github.com/JayGarland/chatgpt-on-wechat/wiki/FAQs) ，其次前往 [Issues](https://github.com/zhayujie/chatgpt-on-wechat/issues) 中搜索。

