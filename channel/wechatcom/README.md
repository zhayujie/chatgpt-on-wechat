
> 详细文档暂无

## 自建应用

- 在企业微信工作台自建应用

建立应用后点击通过API接收消息，设置服务器地址，服务器地址是`http://url:port/wxcomapp`的形式，也可以不用域名，比如 `http://ip:port/wxcomapp`

- 修改配置

在主目录下的`config.json`中填写以下配置项

```python
    # wechatcom的通用配置
    "wechatcom_corp_id": "",  # 企业微信公司的corpID
    # wechatcomapp的配置
    "wechatcomapp_token": "",  # 企业微信app的token
    "wechatcomapp_port": 9898,  # 企业微信app的服务端口,不需要端口转发
    "wechatcomapp_secret": "",  # 企业微信app的secret
    "wechatcomapp_agent_id": "",  # 企业微信app的agent_id
    "wechatcomapp_aes_key": "",  # 企业微信app的aes_key
```

- 运行程序

```python app.py```

在设置服务器页面点击保存

- 添加可信IP

在自建应用管理页下方，将服务器的IP添加到可信IP
