## 插件描述
简易的敏感词插件，暂不支持分词，请自行导入词库到插件文件夹中的`banwords.txt`，每行一个词，一个参考词库是[1](https://github.com/cjh0613/tencent-sensitive-words/blob/main/sensitive_words_lines.txt)。

`config.json`中能够填写默认的处理行为，目前行为有：
- `ignore` : 无视这条消息。
- `replace` : 将消息中的敏感词替换成"*"，并回复违规。

## 致谢
搜索功能实现来自https://github.com/toolgood/ToolGood.Words