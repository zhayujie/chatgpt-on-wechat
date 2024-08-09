# bot_type
OPEN_AI = "openAI"
CHATGPT = "chatGPT"
BAIDU = "baidu"  # 百度文心一言模型
XUNFEI = "xunfei"
CHATGPTONAZURE = "chatGPTOnAzure"
LINKAI = "linkai"
CLAUDEAI = "claude"  # 使用cookie的历史模型
CLAUDEAPI= "claudeAPI"  # 通过Claude api调用模型
QWEN = "qwen"  # 旧版通义模型
QWEN_DASHSCOPE = "dashscope"  # 通义新版sdk和api key


GEMINI = "gemini"  # gemini-1.0-pro
ZHIPU_AI = "glm-4"
MOONSHOT = "moonshot"
MiniMax = "minimax"


# model
CLAUDE3 = "claude-3-opus-20240229"
GPT35 = "gpt-3.5-turbo"
GPT35_0125 = "gpt-3.5-turbo-0125"
GPT35_1106 = "gpt-3.5-turbo-1106"

GPT_4o = "gpt-4o"
GPT4_TURBO = "gpt-4-turbo"
GPT4_TURBO_PREVIEW = "gpt-4-turbo-preview"
GPT4_TURBO_04_09 = "gpt-4-turbo-2024-04-09"
GPT4_TURBO_01_25 = "gpt-4-0125-preview"
GPT4_TURBO_11_06 = "gpt-4-1106-preview"
GPT4_VISION_PREVIEW = "gpt-4-vision-preview"

GPT4 = "gpt-4"
GPT_4o_MINI = "gpt-4o-mini"
GPT4_32k = "gpt-4-32k"
GPT4_06_13 = "gpt-4-0613"
GPT4_32k_06_13 = "gpt-4-32k-0613"

WHISPER_1 = "whisper-1"
TTS_1 = "tts-1"
TTS_1_HD = "tts-1-hd"

WEN_XIN = "wenxin"
WEN_XIN_4 = "wenxin-4"

QWEN_TURBO = "qwen-turbo"
QWEN_PLUS = "qwen-plus"
QWEN_MAX = "qwen-max"

LINKAI_35 = "linkai-3.5"
LINKAI_4_TURBO = "linkai-4-turbo"
LINKAI_4o = "linkai-4o"

GEMINI_PRO = "gemini-1.0-pro"
GEMINI_15_flash = "gemini-1.5-flash"
GEMINI_15_PRO = "gemini-1.5-pro"

MODEL_LIST = [
              GPT35, GPT35_0125, GPT35_1106, "gpt-3.5-turbo-16k",
              GPT_4o, GPT_4o_MINI, GPT4_TURBO, GPT4_TURBO_PREVIEW, GPT4_TURBO_01_25, GPT4_TURBO_11_06, GPT4, GPT4_32k, GPT4_06_13, GPT4_32k_06_13,
              WEN_XIN, WEN_XIN_4,
              XUNFEI, ZHIPU_AI, MOONSHOT, MiniMax,
              GEMINI, GEMINI_PRO, GEMINI_15_flash, GEMINI_15_PRO,
              "claude", "claude-3-haiku", "claude-3-sonnet", "claude-3-opus", "claude-3-opus-20240229", "claude-3.5-sonnet",
              "moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k",
              QWEN, QWEN_TURBO, QWEN_PLUS, QWEN_MAX,
              LINKAI_35, LINKAI_4_TURBO, LINKAI_4o
            ]

# channel
FEISHU = "feishu"
DINGTALK = "dingtalk"
