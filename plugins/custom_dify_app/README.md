# custom_dify_app
ChatGPT on WeChat项目插件，根据群聊环境自动选择相应的Dify应用

支持根据群聊名称关键词自动切换不同的Dify应用，也支持为单聊配置专门的Dify应用

## 插件说明

**插件名称**: custom_dify_app（自定义Dify应用）

**功能描述**: 根据群聊环境自动选择相应的Dify应用。例如，在与AI助手进行私聊时，自动调用企业内部员工助手Dify应用；在xx平台技术支持群中@AI助手时，则自动切换至该平台的技术支持Dify应用。

## 插件使用

1. 将`config.json.template`复制为`config.json`
2. 根据自己的需要修改`config.json`配置文件
3. 在项目的`config.json`中启用该插件

config.json 配置说明
```bash
[
    {
        "app_name": "xx应用",                 # Dify应用名称，仅用于标识
        "app_type": "chatbot",                # Dify应用类型，目前支持 "chatbot", "agent", "workflow"
        "api_base": "https://api.dify.ai/v1", # Dify API 基础URL
        "api_key": "app-xx",                  # Dify应用的API密钥
        "use_on_single_chat": false,          # 是否用于单聊，true/false
        "image_recognition": false,           # 是否启用图片识别，true/false
        "group_name_keywords": [              # 群名关键词列表，当群名包含其中任一关键词时，使用该配置
            "测试群"
        ]
    }
]
```

## 注意事项

1. 插件会根据配置文件中的顺序逐一匹配群名关键词，匹配到第一个符合条件的配置就会停止并使用该配置。
2. 对于单聊，插件会使用配置文件中第一个设置了 `"use_on_single_chat": true` 的配置。
3. `image_recognition` 默认为false，当设置为true后，请确保在对应的Dify应用中已开启图片识别功能。
4. 如果没有找到匹配的配置，插件不会修改上下文，将使用默认的 Dify 配置（如果有的话）。
5. 确保在项目的主配置文件中正确设置了 Dify 相关的配置项，以便插件可以正常工作。
