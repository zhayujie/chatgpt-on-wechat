"""
channel factory
"""
from common import const
from common.log import logger


def create_bot(bot_type):
    """
    create a bot_type instance
    :param bot_type: bot type code
    :return: bot instance
    """
    logger.info(f"正在连接AI模型: {bot_type}")

    try:
        if bot_type == const.BAIDU:
            # 替换Baidu Unit为Baidu文心千帆对话接口
            # from bot.baidu.baidu_unit_bot import BaiduUnitBot
            # return BaiduUnitBot()
            from bot.baidu.baidu_wenxin import BaiduWenxinBot
            logger.info("已连接到百度文心千帆模型")
            return BaiduWenxinBot()

        elif bot_type == const.CHATGPT:
            # ChatGPT 网页端web接口
            from bot.chatgpt.chat_gpt_bot import ChatGPTBot
            logger.info("已连接到ChatGPT网页版")
            return ChatGPTBot()

        elif bot_type == const.OPEN_AI:
            # OpenAI 官方对话模型API
            from bot.openai.open_ai_bot import OpenAIBot
            logger.info("已连接到OpenAI API")
            return OpenAIBot()

        elif bot_type == const.CHATGPTONAZURE:
            # Azure chatgpt service https://azure.microsoft.com/en-in/products/cognitive-services/openai-service/
            from bot.chatgpt.chat_gpt_bot import AzureChatGPTBot
            return AzureChatGPTBot()

        elif bot_type == const.XUNFEI:
            from bot.xunfei.xunfei_spark_bot import XunFeiBot
            return XunFeiBot()

        elif bot_type == const.LINKAI:
            from bot.linkai.link_ai_bot import LinkAIBot
            return LinkAIBot()

        elif bot_type == const.CLAUDEAI:
            from bot.claude.claude_ai_bot import ClaudeAIBot
            return ClaudeAIBot()
        elif bot_type == const.CLAUDEAPI:
            from bot.claudeapi.claude_api_bot import ClaudeAPIBot
            return ClaudeAPIBot()
        elif bot_type == const.QWEN:
            from bot.ali.ali_qwen_bot import AliQwenBot
            return AliQwenBot()
        elif bot_type == const.QWEN_DASHSCOPE:
            from bot.dashscope.dashscope_bot import DashscopeBot
            return DashscopeBot()
        elif bot_type == const.GEMINI:
            from bot.gemini.google_gemini_bot import GoogleGeminiBot
            return GoogleGeminiBot()

        elif bot_type == const.ZHIPU_AI:
            from bot.zhipuai.zhipuai_bot import ZHIPUAIBot
            return ZHIPUAIBot()

        elif bot_type == const.MOONSHOT:
            from bot.moonshot.moonshot_bot import MoonshotBot
            return MoonshotBot()

        elif bot_type == const.MiniMax:
            from bot.minimax.minimax_bot import MinimaxBot
            return MinimaxBot()

        elif bot_type == const.OLLAMA:
            from bot.ollama.ollama_bot import OllamaBot
            logger.info("已连接到Ollama本地模型")
            return OllamaBot()

        logger.error(f"未知的AI模型类型: {bot_type}")
        raise RuntimeError(f"未知的AI模型类型: {bot_type}")

    except Exception as e:
        logger.error(f"连接AI模型 {bot_type} 失败: {str(e)}")
        raise e
