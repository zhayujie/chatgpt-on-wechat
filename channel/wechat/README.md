**本项目接入微信目前有`itchat`、`wechaty`、`wechatferry`三种协议，其中前两个协议目前（2025年3月）已经无法使用，遂新增 [WechatFerry](https://github.com/lich0821/WeChatFerry) 协议。**

## WechatFerry 协议
### 准备工作

1. 使用该协议接入微信，需要使用特定版本的`windows`客户端，具体因协议的版本而异，目前使用的是`wcferry == 39.4.1.0`，对应的wx客户端版本为`3.9.12.17`，[下载链接](https://github.com/lich0821/WeChatFerry/releases/download/v39.4.1/WeChatSetup-3.9.12.17.exe) 

   下载后安装并登录，**关闭系统自动更新**  （wx客户端版本降级不影响历史聊天数据）
2. python版本:`Python>=3.9`，建议3.9或3.10即可，[3.10.10下载链接](https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe) ，

   安装时候记得勾选 `add to path`。

### 克隆项目
```
git clone https://github.com/zhayujie/chatgpt-on-wechat
```
如果克隆失败或者无法克隆，可以下载压缩包到本地解压

### 安装依赖
切换到项目更目录，执行下面的命令：
```
pip3 install -r requirements.txt 
pip3 install -r requirements-optional.txt 
```
### 配置
配置文件的模板在根目录的 `config-template.json` 中，需复制该模板创建最终生效的 `config.json` 文件，执行下面的命令或者手动复制并重命名 
```
copy config-template.json config.json
```
设置启动通道：`"channel_type": "wcf"`， 其他配置参考项目[配置说明](https://docs.link-ai.tech/cow/quick-start/config)

### 启动
直接在项目根目录下执行：
```
python3 app.py  
```
执行后，正常应会提示”微信登录成功，当前用户xxxx“。

如果执行后无反应，说明python解释器的系统变量不是`python3`， 可以尝试`py app.py`等；如果有报错，请检查版本是否正确，以及自行咨询AI尝试解决。


### ⚠ 免责声明
>1. **本工具为开源项目，仅提供基础功能，供用户进行合法的学习、研究和非商业用途**。  
   禁止将本工具用于任何违法违规行为。
>2. **二次开发者的责任**  
>   - 任何基于本工具进行的二次开发、修改或衍生产品，其行为及后果由二次开发者独立承担，与本工具原作者无关。  
>   - **禁止** 使用贡献者的姓名、项目名称或相关信息作为二次开发产品的营销或推广手段。  
>   - 建议二次开发者在其衍生产品中添加自己的责任声明，明确责任归属。
>3. **用户责任**  
>   - 使用本工具或其衍生产品的所有后果由用户自行承担，原作者不对因直接或间接使用本工具而导致的任何损失、责任或争议负责。
>4. **法律法规**  
>   - 用户和二次开发者须遵守《中华人民共和国网络安全法》、《中华人民共和国数据安全法》等相关法律法规。  
>   - 本工具涉及的所有第三方商标或产品名称，其权利归权利人所有，作者与第三方无任何直接或间接关系。
>5. **作者保留权利**  >
>   - 本工具原作者保留修改、更新、删除该类工具的权利，无需事先通知或承担任何义务。
