## 插件说明：
一个简易的实现输入特定开始字符：$(语种)$+你的内容,直接触发机器人合成对应语种语音,实现自由切换zure的多语种合成插件

## 使用方法：
$(语种)$+你的内容,如：$(美式英文)$+你好，机器人会以美式语音回复，
支持的语种可在voice.azure_voice.py中的chooose_voice()函数中查看，
可自行结合azure的语音库自行添加人物语种，对应的人物名字可见：https://speech.microsoft.com/portal/a9f4d941f1eb426290c2073472be29f7/voicegallery
打开对应人物的示例代码，copy对应的voice名字即可，speech_config.speech_synthesis_voice_name = "ja-JP-AoiNeural"中的ja-JP-AoiNeural即为人物名字


## 使用前提：
语音合成引擎选择azure