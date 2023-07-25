## 插件描述

本插件依赖主要项目[chatgpt-on-wechat](https://github.com/zhayujie/chatgpt-on-wechat),用于将画图请求转发给`Midjourney` api，插件依赖于[midjourney-proxy](https://github.com/novicezk/midjourney-proxy)提供的服务转发,具体搭建方法请参考原项目。

**支持个人微信和公众号，公众号需要认证后消息通道设置为wechatmp_service使用效果最佳！**

## 使用说明

​	具体搭建方法就不细说了，没有搭建[midjourney-proxy](https://github.com/novicezk/midjourney-proxy)的无法使用本插件，配置可选内容请自行参考项目文档，支持返回原图链接和短链，建议短链和接口API都配置、如果使用了cdn反代，建议开启http鉴权。

#### 使用前提

1. 注册 MidJourney，创建自己的频道，参考 https://docs.midjourney.com/docs/quick-start
2. 获取用户Token、服务器ID、频道ID：[获取方式](https://github.com/novicezk/midjourney-proxy/blob/main/docs/discord-params.md)
3. 搭建[midjourney-proxy](https://github.com/novicezk/midjourney-proxy)，请根据项目教程部署，先完成以上两步
4. 搭建成功后输入ip:端口号/mj，能正常打开既是部署成功
5. 搞不定的可以联系我bot，我有空会帮忙搭建一下，或者直接付费使用我的api

#### 插件安装

将本项目文件下载后，重命名为“midjourney_turbo”，然后整个文件放入到chatgpt-on-wechat/plugins目录即可配合项目使用

将`config.json.template`复制为`config.json`，修改其中的参数和规则。

```json
{
    "domain_name":"",    		# 填写Midjourney Proxy的域名和端口，如：http://127.0.0.1:8080
    "api_key":"",   			# Midjourney Proxy如果有设置api_key，可以配置
    "image_ins":"/p",  	  		# 垫图指令，如无特殊需求可以默认
    "blend_ins":"/b",      	 	# 合图指令，如无特殊需求可以默认
    "change_ins":"/c",   		# 改变或放大指令，如无特殊需求可以默认（配合V/U）
       "default_params": {
        "action": "IMAGINE:出图",
        "prompt": ""        	#  可以预设prompt，此处可以默认
  },
    "gpt_optimized": true,  	# Gpt优化画图的开关选项
    "short_url_api":"",     	# 短链API，如无短链接口无需配置，短链配置选用“Url-Shorten-Worker”项目
    "split_url":false,      	# 这里涉及到反代域名的操作，如无特殊需求保持默认即可
    "lock":true,                # 是否开启使用次数限制 ！！未适配公众号！！
    "group_lock":false,			# 是否开启群聊使用限制，个人和群聊同步，即个人次数满了，群聊也不行  ！！未适配公众号！！
    "trial_lock":2,				# 使用次数的限制   ！！未适配公众号！！
    "complete_prompt": "\n\uD83E\uDD42任务完成！\n⌚\uFE0F任务耗时{start_finish},总耗时{submit_finish}\n--------------------------------\n\uD83C\uDD94任务ID:{id}\n--------------------------------\n\uD83D\uDCE7回复以下指令衍生或选图\uD83D\uDCE7\n\n画 /ins {id} V1\n画 /ins {id} V2\n画 /ins {id} V3\n画 /ins {id} V4\n画 /ins {id} U1\n画 /ins {id} U2\n画 /ins {id} U3\n画 /ins {id} U4\n\n--------------------------------\n\uD83D\uDC49V1～V4(衍生图片)\n\uD83D\uDC49U1～U4(确认选图)\n\u200D\uD83D\uDCBBTip：左上到右下依次为1234\n--------------------------------\n\uD83C\uDF20如果不出图片，请点击原图链接：\n{imgurl}"         # 画图完成提示词，注意占位符格式和变量名   
}
```

### 画图请求

> - [x] 支持变换指令，默认 /c 命令+任务ID进行变换
> - [x] 支持垫图指令，默认 /p 命令+关键词内容进行垫图创作
> - [x] 支持合图指令，默认 /b 命令+图片数量进行合图创作，即blen功能
> - [x] 插件为有效防止send图片的报错和超时，对图片大小进行了下载并压缩，添加了send报错异常重试
> - [x] 建议开启GPT优化关键词功能，丝滑出图，如不选用请参考下方
> - [x] midjourney-proxy直接提供了百度翻译，建议在搭建的时候就配置上百度翻译的参数，插件就不额外加载百度翻译

用户的画图和各种命令的请求格式为:

```
    <画图触发词>:<prompt>			如：画中国的小女孩
    <画图触发词> /c ID V/U1-4		如：画 /c 6076066202174582 V1
    <画图触发词> /b 数量		 	   如：画 /b 3
    <画图触发词> /p <prompt>			如：画 /p 猫
```

## 使用示例

画图

![](https://github.com/chazzjimel/midjourney_turbo/blob/main/doc/images/001.png)

垫图

![](https://github.com/chazzjimel/midjourney_turbo/blob/main/doc/images/002.png)

合图

![](https://github.com/chazzjimel/midjourney_turbo/blob/main/doc/images/003.png)

变换

![](https://github.com/chazzjimel/midjourney_turbo/blob/main/doc/images/005.png)

- **请注意本插件会在项目主目录的tmp文件夹进行保存图片和压缩操作，由于插件无法在发送后自动删除，建议定期清理**



------



**如果本插件好用，请给star，由于Bot被举报，所以插件停止更新，拜拜~**
