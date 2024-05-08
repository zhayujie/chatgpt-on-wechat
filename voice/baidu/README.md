## 说明
百度语音识别与合成参数说明
百度语音依赖，经常会出现问题，可能就是缺少依赖：
pip install baidu-aip
pip install pydub
pip install pysilk
还有 ffmpeg，不同系统安装方式不同

系统中收到的语音文件为 mp3 格式（wx）或者 sil 格式（wxy），如果要识别需要转换为 pcm 格式，转换后的文件为 16k 采样率，单声道，16bit 的 pcm 文件
发送时又需要（wx）转换为 mp3 格式，转换后的文件为 16k 采样率，单声道，16bit 的 pcm 文件，（wxy）转换为 sil 格式，还要计算声音长度，发送时需要带上声音长度
这些事情都在 audio_convert.py 中封装了，直接调用即可


参数说明
识别参数
https://ai.baidu.com/ai-doc/SPEECH/Vk38lxily
合成参数
https://ai.baidu.com/ai-doc/SPEECH/Gk38y8lzk

## 使用说明
分两个地方配置

1、对于 def voiceToText(self, filename) 函数中调用的百度语音识别 API，中接口调用 asr（参数）这个配置见 CHATGPT-ON-WECHAT 工程目录下的`config.json`文件和 config.py 文件。
参数	    可需	描述
app_id    必填	应用的 APPID
api_key  必填	应用的 APIKey
secret_key  必填	应用的 SecretKey
dev_pid	    必填	语言选择，填写语言对应的 dev_pid 值

2、对于 def textToVoice(self, text) 函数中调用的百度语音合成 API，中接口调用 synthesis（参数）在本目录下的`config.json`文件中进行配置。
参数	    可需	描述
tex	        必填	合成的文本，使用 UTF-8 编码，请注意文本长度必须小于 1024 字节  
lan	        必填	固定值 zh。语言选择，目前只有中英文混合模式，填写固定值 zh
spd	        选填	语速，取值 0-15，默认为 5 中语速
pit	        选填	音调，取值 0-15，默认为 5 中语调
vol	        选填	音量，取值 0-15，默认为 5 中音量（取值为 0 时为音量最小值，并非为无声）
per（基础音库）	选填	度小宇=1，度小美=0，度逍遥（基础）=3，度丫丫=4
per（精品音库）	选填	度逍遥（精品）=5003，度小鹿=5118，度博文=106，度小童=110，度小萌=111，度米朵=103，度小娇=5
aue	        选填	3 为 mp3 格式 (默认)；4 为 pcm-16k；5 为 pcm-8k；6 为 wav（内容同 pcm-16k）; 注意 aue=4 或者 6 是语音识别要求的格式，但是音频内容不是语音识别要求的自然人发音，所以识别效果会受影响。

关于 per 参数的说明，注意您购买的哪个音库，就填写哪个音库的参数，否则会报错。如果您购买的是基础音库，那么 per 参数只能填写 0 到 4，如果您购买的是精品音库，那么 per 参数只能填写 5003，5118，106,110,111,103,5 其他的都会报错。
### 配置文件

将文件夹中`config.json.template`复制为`config.json`。

``` json
    {
    "lang": "zh",
    "ctp": 1,
    "spd": 5,
    "pit": 5,
    "vol": 5,
    "per": 0
    }
```