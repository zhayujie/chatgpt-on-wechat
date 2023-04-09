## 插件描述

本插件用于将画图请求转发给`replicate` api。

## 使用说明

在 [`Replicate`](https://replicate.com/)获取`API Token`，

将`config.json.template`复制为`config.json`，修改`API token`，并修改其中的参数和规则。

`Railway`支持使用环境变量(`replicate_api_token`或`REPLICATE_API_TOKEN`)方式传递`API token`，

### 画图请求格式

> 请**注意**，你需要满足每个`model`规定的`API`限制。
> 比如: [`anything-v3`](https://replicate.com/cjwbw/anything-v3-better-vae/api) 不支持384的长宽。

以下是另一个插件`sdwebui`的说明，关键词覆盖的逻辑一样，先拿来用。

用户的画图请求格式为:

```
    <画图触发词><关键词1> <关键词2> ... <关键词n>:<prompt> 
```

- 本插件会对画图触发词后的关键词进行逐个匹配，如果触发了规则中的关键词，则会在画图请求中重载对应的参数。
- 规则的匹配顺序参考`config.json`中的顺序，每个关键词最多被匹配到1次，如果多个关键词触发了重复的参数，重复参数以最后一个关键词为准。
- 关键词中包含`help`或`帮助`，会打印出帮助文档。

第一个"**:**"号之后的内容会作为附加的**prompt**，接在最终的prompt后。

例如: 画横版 高清 二次元:cat

会触发三个关键词 "横版", "高清", "二次元"，prompt为"cat"

若默认参数是:
```json
    "width": 512,
    "height": 512,
    "enable_hr": false,
    "prompt": "8k"
    "negative_prompt": "nsfw",
    "sd_model_checkpoint": "perfectWorld_v2Baked"
```

"横版"触发的规则参数为:
```json
    "width": 640,
    "height": 384,
```

"高清"触发的规则参数为:
```json
    "enable_hr": true,
    "hr_scale": 1.6,
```

"二次元"触发的规则参数为:
```json
    "negative_prompt": "(low quality, worst quality:1.4),(bad_prompt:0.8), (monochrome:1.1), (greyscale)",
    "steps": 20,
    "prompt": "masterpiece, best quality",

    "sd_model_checkpoint": "meinamix_meinaV8"
```

以上这些规则的参数会和默认参数合并。第一个":"后的内容cat会连接在prompt后。

得到最终参数为:
```json
    "width": 640,
    "height": 384,
    "enable_hr": true,
    "hr_scale": 1.6,
    "negative_prompt": "(low quality, worst quality:1.4),(bad_prompt:0.8), (monochrome:1.1), (greyscale)",
    "steps": 20,
    "prompt": "masterpiece, best quality, cat",
    
    "sd_model_checkpoint": "meinamix_meinaV8"
```
