## 插件说明

基于 LinkAI 提供的知识库、Midjourney绘画等能力对机器人的功能进行增强。平台地址: https://chat.link-ai.tech/console

## 插件配置

将 `plugins/linkai` 目录下的 `config.json.template` 配置模板复制为最终生效的 `config.json`:

以下是配置项说明：

```bash
{
    "group_app_map": {            # 群聊 和 应用编码 的映射关系
        "测试群1": "default",      # 表示在名称为 "测试群1" 的群聊中将使用app_code 为 default 的应用
        "测试群2": "Kv2fXJcH"
    },
    "midjourney": {
        "enabled": true,          # midjourney 绘画开关
        "auto_translate": true,   # 是否自动将提示词翻译为英文
        "img_proxy": true,        # 是否对生成的图片使用代理，如果你是国外服务器，将这一项设置为false会获得更快的生成速度
        "max_tasks": 3,           # 支持同时提交的总任务个数
        "max_tasks_per_user": 1,  # 支持单个用户同时提交的任务个数
        "use_image_create_prefix": true   # 是否使用全局的绘画触发词，如果开启将同时支持由`config.json`中的 image_create_prefix 配置触发
    }
}

```
注意：

 - 配置项中 `group_app_map` 部分是用于映射群聊与LinkAI平台上的应用， `midjourney` 部分是 mj 画图的配置，可根据需要进行填写，未填写配置时默认不开启相应功能
 - 实际 `config.json` 配置中应保证json格式，不应携带 '#' 及后面的注释
 - 如果是`docker`部署，可通过映射 `plugins/config.json` 到容器中来完成插件配置，参考[文档](https://github.com/zhayujie/chatgpt-on-wechat#3-%E6%8F%92%E4%BB%B6%E4%BD%BF%E7%94%A8)

## 插件使用

> 使用插件中的知识库管理功能需要首先开启`linkai`对话，依赖全局 `config.json` 中的 `use_linkai` 和 `linkai_api_key` 配置；而midjourney绘画功能则只需填写 `linkai_api_key` 配置，`use_linkai` 无论是否关闭均可使用。具体可参考 [详细文档](https://link-ai.tech/platform/link-app/wechat)。

完成配置后运行项目，会自动运行插件，输入 `#help linkai` 可查看插件功能。

### 1.知识库管理功能

提供在不同群聊使用不同应用的功能。可以在上述 `group_app_map` 配置中固定映射关系，也可以通过指令在群中快速完成切换。

应用切换指令需要首先完成管理员 (`godcmd`) 插件的认证，然后按以下格式输入：

`$linkai app {app_code}`

例如输入 `$linkai app Kv2fXJcH`，即将当前群聊与 app_code为 Kv2fXJcH 的应用绑定。

另外，还可以通过 `$linkai close` 来一键关闭linkai对话，此时就会使用默认的openai接口；同理，发送 `$linkai open` 可以再次开启。

### 2.Midjourney绘画功能

指令格式：

```
 - 图片生成: $mj 描述词1, 描述词2..
 - 图片放大: $mju 图片ID 图片序号
 - 图片变换: $mjv 图片ID 图片序号
 - 重置: $mjr 图片ID
```

例如：

```
"$mj a little cat, white --ar 9:16"
"$mju 1105592717188272288 2"
"$mjv 11055927171882 2"
"$mjr 11055927171882"
```

注：
1. 开启 `use_image_create_prefix` 配置后可直接复用全局画图触发词，以"画"开头便可以生成图片。
2. 提示词内容中包含敏感词或者参数格式错误可能导致绘画失败，生成失败不消耗积分
3. 使用 `$mj open` 和 `$mj close` 指令可以快速打开和关闭绘图功能
