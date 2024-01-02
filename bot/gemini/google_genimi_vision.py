import google.generativeai as genai

from bot.session_manager import SessionManager
from bridge.reply import Reply,ReplyType
from bot.baidu.baidu_wenxin_session import BaiduWenxinSession
from common.log import logger
from common import memory
from config import conf
import PIL.Image


# GOOGLE_GEMINI提供的图像识别接口
class GeminiVision(object):
    def __init__(self):
        super().__init__()
        self.api_key=conf().get('gemini_api_key')
        # 复用文心的token计算方式
        self.sessions = SessionManager(BaiduWenxinSession,model=conf().get('model') or 'gpt=3.5-turbo')

    def do_vision_completion_if_need(self, session_id: str, query: str):
        '''Request text response from multimodal input with google-generativeai's gemini-pro-vision'''
        img_cache = memory.USER_IMAGE_CACHE.get(session_id)
        if img_cache and conf().get("image_recognition"):
            response, err = self.vision_completion(query, img_cache)
            memory.USER_IMAGE_CACHE[session_id] = None
            if err:
                logger.error(f"[GEMINI] fetch reply error, {err}")
                reply_text = f'获取gemini-pro-vision多模态响应时出错,{err}'
                return Reply(ReplyType.TEXT, reply_text)
            else:
                reply_text = response.text
                self.sessions.session_reply(reply_text, session_id)
                logger.info(f"[GEMINI] reply={reply_text}")
                return Reply(ReplyType.TEXT, reply_text)
        return None

    def vision_completion(self, query: str, img_cache: dict):
        msg = img_cache.get("msg")
        path = img_cache.get("path")
        msg.prepare()
        logger.info(f"[GEMINI] query with images, path={path}")
        
        try:
            genai.configure(api_key=self.api_key,transport='rest')

            # Set up the model
            generation_config = {
            "temperature": 0.4,
            "top_p": 1,
            "top_k": 32,
            "max_output_tokens": 4096,
            }

            safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            ]
            model = genai.GenerativeModel(
                model_name='gemini-pro-vision',
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            img = PIL.Image.open(path)
            res = model.generate_content([query,img])
            return res,None
        except Exception as e:
            return None, e
