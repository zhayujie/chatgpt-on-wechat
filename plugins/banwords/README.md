
## 插件描述

简易的敏感词插件，暂不支持分词，请自行导入词库到插件文件夹中的`banwords.txt`，每行一个词，一个参考词库是[1](https://github.com/cjh0613/tencent-sensitive-words/blob/main/sensitive_words_lines.txt)。

使用前将`config.json.template`复制为`config.json`，并自行配置。

目前插件对消息的默认处理行为有如下两种：

- `ignore` : 无视这条消息。
- `replace` : 将消息中的敏感词替换成"*"，并回复违规。

```json
    "action": "replace",  
    "reply_filter": true,
    "reply_action": "ignore"
```

在以上配置项中：

- `action`: 对用户消息的默认处理行为
- `reply_filter`: 是否对ChatGPT的回复也进行敏感词过滤
- `reply_action`: 如果开启了回复过滤，对回复的默认处理行为

## 致谢

搜索功能实现来自https://github.com/toolgood/ToolGood.Words