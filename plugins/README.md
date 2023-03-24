# 插件说明
本项目主体是调用ChatGPT接口的Wechat自动回复机器人。之前未插件化的代码耦合程度高，很难定制一些个性化功能（如流量控制、接入本地的NovelAI画图平台等），多个功能的优先级顺序也难以调度。
**插件化**: 在保证主体功能是ChatGPT的前提下，推荐将主体功能外的功能分离成不同的插件。有个性化需求的用户仅需按照插件提供的接口编写插件，无需了解程序主体的代码结构，同时也方便代码的测试和调试。（插件调用目前仅支持 itchat）

## 插件触发时机

### 消息处理过程
了解插件触发时机前，首先需要了解程序收到消息后的执行过程。插件化版本的消息处理过程如下：
```
    1.收到消息 ---> 2.产生回复 ---> 3.包装回复 ---> 4.发送回复
```
以下是它们的默认处理逻辑(太长不看，可跳过)：

- 1. 收到消息
    本过程接收到用户消息，根据用户设置，判断本条消息是否触发。若触发，则判断该消息的命令类型，如声音、聊天、画图等。之后，将消息包装成如下的 Context 交付给下一个步骤。
    ```python
    class ContextType (Enum):
        TEXT = 1         # 文本消息
        VOICE = 2        # 音频消息
        IMAGE_CREATE = 3 # 创建图片命令
    class Context:
        def __init__(self, type : ContextType = None , content = None,  kwargs = dict()):
            self.type = type
            self.content = content
            self.kwargs = kwargs
        def __getitem__(self, key):
            return self.kwargs[key]
    ```
    `Context`中除了存放消息类型和内容外,还存放了与会话相关的参数。一个例子是，当收到用户私聊消息时，还会存放以下的会话参数，`isgroup`标识`Context`是否时群聊消息，`msg`是`itchat`中原始的消息对象，`receiver`是应回复消息的对象ID，`session_id`是会话ID(一般是触发bot的消息发送方，群聊中如果`conf`里设置了`group_chat_in_one_session`，那么此处便是群聊的ID)
    ```
        context.kwargs = {'isgroup': False, 'msg': msg, 'receiver': other_user_id, 'session_id': other_user_id}
    ```
2. 产生回复
    本过程用于处理消息。目前默认处理逻辑如下，它根据`Context`的类型交付给对应的bot。如果本过程未产生任何回复，则会跳过之后的处理阶段。
    ```python
    if context.type == ContextType.TEXT or context.type == ContextType.IMAGE_CREATE:
        reply = super().build_reply_content(context.content, context) #文字跟画图交付给chatgpt
    elif context.type == ContextType.VOICE: # 声音先进行语音转文字后，修改Context类型为文字后，再交付给chatgpt
        msg = context['msg']
        file_name = TmpDir().path() + context.content
        msg.download(file_name)
        reply = super().build_voice_to_text(file_name)
        if reply.type != ReplyType.ERROR and reply.type != ReplyType.INFO:
            context.content = reply.content # 语音转文字后，将文字内容作为新的context
            context.type = ContextType.TEXT
            reply = super().build_reply_content(context.content, context)
            if reply.type == ReplyType.TEXT:
                if conf().get('voice_reply_voice'):
                    reply = super().build_text_to_voice(reply.content)
    ```
    Bot可产生的回复如下所示，它允许Bot可以回复多类不同的消息，未来可能不止能返回文字，而是能根据文字回复音频/图片，这时候便能派上用场。同时也加入了`INFO`和`ERROR`消息类型区分系统提示和系统错误。
    ```python
    class ReplyType(Enum):
        TEXT = 1        # 文本
        VOICE = 2       # 音频文件
        IMAGE = 3       # 图片文件
        IMAGE_URL = 4   # 图片URL
        
        INFO = 9
        ERROR = 10
    class Reply:
        def __init__(self, type : ReplyType = None , content = None):
            self.type = type
            self.content = content
    ```
3. 装饰回复
    本过程根据`Context`和回复的类型，对回复的内容进行装饰。目前的装饰有以下两种，如果是文本回复，会根据是否在群聊中来决定是否艾特收方或添加回复前缀。
    如果是`INFO`或`ERROR`类型，会在消息前添加对应字样。
    ```python
    if reply.type == ReplyType.TEXT:
        reply_text = reply.content
        if context['isgroup']:
            reply_text = '@' +  context['msg']['ActualNickName'] + ' ' + reply_text.strip()
            reply_text = conf().get("group_chat_reply_prefix", "")+reply_text
        else:
            reply_text = conf().get("single_chat_reply_prefix", "")+reply_text
        reply.content = reply_text
    elif reply.type == ReplyType.ERROR or reply.type == ReplyType.INFO:
        reply.content = str(reply.type)+":\n" + reply.content
    ```
4. 发送回复
    本过程根据回复的类型来发送回复给接收方`context["receiver"]`。

### 插件触发事件

主程序会在各消息处理过程之间触发插件事件，插件可以监听相应事件编写相应的处理逻辑。
```
    1.收到消息 ---> 2.产生回复 ---> 3.包装回复 ---> 4.发送回复
```
目前加入了三类事件的触发：
```
1.收到消息 
---> `ON_HANDLE_CONTEXT` 
2.产生回复 
---> `ON_DECORATE_REPLY` 
3.包装回复 
---> `ON_SEND_REPLY` 
4.发送回复
```
触发事件会产生事件上下文`EventContext`，它包含了以下信息:
`EventContext(Event事件类型, {'channel' : 消息channel, 'context': context, 'reply': reply})`

插件的处理函数可以修改`Context`和`Reply`的内容来定制化处理逻辑。

## 插件编写
以`plugins/hello`为例，它编写了一个简单`Hello`插件。

1. 创建插件
在`plugins`目录下创建一个插件文件夹，例如`hello`。然后，在该文件夹中创建一个与文件夹同名的`.py`文件，例如`hello.py`。
```
plugins/
└── hello
    ├── __init__.py
    └── hello.py
```

2. 编写插件类
在`hello.py`文件中，创建插件类，它继承自Plugin类。在类定义之前使用`@plugins.register`装饰器注册插件，并填写插件的相关信息，其中`desire_priority`表示插件默认的优先级，越大优先级越高，扫描到插件后可在`plugins/plugins.json`中修改插件优先级。并在`__init__`中绑定你编写的事件处理函数：
```python
@plugins.register(name="Hello", desc="A simple plugin that says hello", version="0.1", author="lanvent", desire_priority= -1)
class Hello(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[Hello] inited")
```

3. 编写事件处理函数
事件处理函数接收一个`EventContext`对象作为参数。`EventContext`对象包含了事件相关的信息，如消息内容和当前回复等。可以通过`e_context['key']`访问这些信息。

处理函数中，你可以修改`EventContext`对象的信息，比如更改回复内容。在处理函数结束时，需要设置`EventContext`对象的`action`属性，以决定如何继续处理事件。有以下三种处理方式：
- `EventAction.CONTINUE`: 事件未结束，继续交给下个插件处理，如果没有下个插件，则交付给默认的事件处理逻辑。
- `EventAction.BREAK`: 事件结束，不再给下个插件处理，交付给默认的处理逻辑。
- `EventAction.BREAK_PASS`: 事件结束，不再给下个插件处理，跳过默认的处理逻辑。

以`Hello`插件为例，它处理`Context`类型为`TEXT`的消息：
- 如果内容是`Hello`，直接将回复设置为`Hello+用户昵称`，并跳过之后的插件和默认逻辑。
- 如果内容是`End`，它会将`Context`的类型更改为`IMAGE_CREATE`，并让事件继续，如果最终交付到默认逻辑，会调用默认的画图Bot来画画。
```python
    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.TEXT:
            return
        content = e_context['context'].content
        if content == "Hello":
            reply = Reply()
            reply.type = ReplyType.TEXT
            msg = e_context['context']['msg']
            if e_context['context']['isgroup']:
                reply.content = "Hello, " + msg['ActualNickName'] + " from " + msg['User'].get('NickName', "Group")
            else:
                reply.content = "Hello, " + msg['User'].get('NickName', "My friend")
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS # 事件结束，并跳过处理context的默认逻辑
        if content == "End":
            # 如果是文本消息"End"，将请求转换成"IMAGE_CREATE"，并将content设置为"The World"
            e_context['context'].type = ContextType.IMAGE_CREATE
            content = "The World"
            e_context.action = EventAction.CONTINUE  # 事件继续，交付给下个插件或默认逻辑
```

## 插件设计规范
- 个性化功能推荐设计为插件。
- 一个插件目录建议只注册一个插件类。建议使用单独的仓库维护插件，便于更新。
- 插件的config文件、使用说明`README.md`、`requirement.txt`放置在插件目录中。
- 默认优先级不要超过管理员插件`Godcmd`的优先级(999)，`Godcmd`插件提供了配置管理、插件管理等功能。