## 插件描述
一个能让chatgpt联网，搜索，数字运算的插件，将赋予强大且丰富的扩展能力  
### 本插件所有工具同步存放至专用仓库：[chatgpt-tool-hub](https://github.com/goldfishh/chatgpt-tool-hub)
  
  
## 使用说明
使用该插件后将默认使用4个工具, 无需额外配置长期生效： 
### 1. python_repl  
###### python解释器，使用它来解释执行python指令
  
### 2. requests
###### 往往用来获取某个网站具体内容

### 3. terminal
###### 在你运行的电脑里执行shell命令

### 4. meteo-weather
###### 回答你有关天气的询问, 本工具使用了[meteo open api](https://open-meteo.com/)


## 使用本插件对话（prompt）技巧 
### 1. 有指引的询问 
#### 例如：
- 总结这个链接的内容 https://www.36kr.com/p/2186160784654466 
- 使用Terminal执行curl cip.cc 
- 借助python_repl和meteo-weather获取深圳天气情况 
  
### 2. 使用搜索引擎工具
- 如果有这个工具就能让chatgpt在不理解某个问题时去使用  
  
  
## 其他插件
###### 除上述以外还有其他插件，比如搜索联网、数学运算、百科、新闻需要获取api-key, 
###### 由于这些插件使用方法暂时还在整理中，如果你不熟悉请不要尝试使用这些工具


## config 配置说明
###### 一个例子
```json
{
  "tools": ["wikipedia"],
  "kwargs": {
      "top_k_results": 2
  }
}
```
- `tools`：本插件初始化时加载的工具, 目前可选集：["wikipedia", "wolfram-alpha", "google-search", "news-api"]
- `kwargs`：工具执行时的配置，一般在这里存放api-key
  
  
## 备注
- 请不要使用本插件做危害他人的事情，请自行判断本插件输出内容的真实性
- 未来一段时间我会实现一些有意思的工具，比如stable diffusion 中文prompt翻译、cv方向的模型推理，欢迎有想法的朋友关注，一起扩展这个项目
