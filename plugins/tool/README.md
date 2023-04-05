## 插件描述
一个能让chatgpt联网，搜索，数字运算的插件，将赋予强大且丰富的扩展能力   
使用该插件需在触发机器人回复条件时，在对话内容前加$tool  
### 本插件所有工具同步存放至专用仓库：[chatgpt-tool-hub](https://github.com/goldfishh/chatgpt-tool-hub)
  
  
## 使用说明
使用该插件后将默认使用4个工具, 无需额外配置长期生效： 
### 1. python 
###### python解释器，使用它来解释执行python指令，可以配合你想要chatgpt生成的代码输出结果或执行事务
  
### 2. requests
###### 往往用来获取某个网站具体内容，结果可能会被反爬策略影响

### 3. terminal
###### 在你运行的电脑里执行shell命令，可以配合你想要chatgpt生成的代码使用，给予自然语言控制手段

### 4. meteo-weather
###### 回答你有关天气的询问, 需要获取时间、地点上下文信息，本工具使用了[meteo open api](https://open-meteo.com/)
注：该工具需提供时间，地点信息，获取的数据不保证准确性

## 使用本插件对话（prompt）技巧 
### 1. 有指引的询问 
#### 例如：
- 总结这个链接的内容 https://github.com/goldfishh/chatgpt-tool-hub 
- 使用Terminal执行curl cip.cc
- 使用python查询今天日期
  
### 2. 使用搜索引擎工具
- 如果有搜索工具就能让chatgpt获取到你的未传达清楚的上下文信息，比如chatgpt不知道你的地理位置，现在时间等，所以无法查询到天气
  
## 其他工具

### 5. wikipedia
###### 可以回答你想要知道确切的人事物

### 6. news *
###### 从全球 80,000 多个信息源中获取当前和历史新闻文章

### 7. bing-search *
###### bing搜索引擎，从此你不用再烦恼搜索要用哪些关键词

### 8. wolfram-alpha *
###### 知识搜索引擎、科学问答系统，常用于专业学科计算

###### 注1：带*工具需要获取api-key才能使用，部分工具需要外网支持   
#### [申请方法](https://github.com/goldfishh/chatgpt-tool-hub/blob/master/docs/apply_optional_tool.md)
  
## config.json 配置说明
###### 默认工具无需配置，其它工具需手动配置，一个例子：
```json
{
  "tools": ["wikipedia"],
  "kwargs": {
      "top_k_results": 2,
      "no_default": false,
      "model_name": "gpt-3.5-turbo"
  }
}
```
注：config.json文件非必须，未创建仍可使用本tool    
- `tools`：本插件初始化时加载的工具, 目前可选集：["wikipedia", "wolfram-alpha", "bing-search", "google-search", "news"]，其中后4个工具需要申请服务api
- `kwargs`：工具执行时的配置，一般在这里存放api-key，或环境配置
  - `no_default`: 用于配置默认加载4个工具的行为，如果为true则仅使用tools列表工具，不加载默认工具
  - `top_k_results`: 控制所有有关搜索的工具返回条目数，数字越高则参考信息越多，但无用信息可能干扰判断，该值一般为2
  - `model_name`: 用于控制tool插件底层使用的llm模型，目前暂未测试3.5以外的模型，一般保持默认
  
  
## 备注
- 强烈建议申请搜索工具搭配使用，推荐bing-search
- 虽然我会有意加入一些限制，但请不要使用本插件做危害他人的事情，请提前了解清楚某些内容是否会违反相关规定，建议提前做好过滤
- 未来一段时间我会实现一些有意思的工具，比如stable diffusion 中文prompt翻译、cv方向的模型推理，欢迎有想法的朋友关注，一起扩展这个项目
