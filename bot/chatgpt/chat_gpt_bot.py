import time
from bot.bot import Bot
from revChatGPT.revChatGPT import Chatbot
from common.log import logger

config = {
    "Authorization": "<Your Bearer Token Here>",  # This is optional
    "session_token": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..yUEdyIPaNgrKerHa.hQfnBM6Ry2npNvakpj1TL_4wr7fuMeLMWOmy-yOSzJxJw7DNyq5vwKeZBwOzthFBIuSu_CpHvYCK_SvRy2RW0gtjPh1XZMxoXejzwJ8VJaVrj3BjarIJdMKRaIHrFwYlRj6fdWa_nGWeueGf1EDE71aSHf4La-4YjoEX8Ou68XHXEsOYQqMuk06u8Wa_aRq5UAj3Clc99dEw3iHU7xvf8lMmB3T1G1LMaubH21niQj-76pUzlf1Kq278Yl8Q6fOGD_CA7mCvnA1LGYzo7u0P5A8dd-p7K3Oqbxw3Gn2TMyEkzZ2q_rTqSJwnbRG87SEYp5Y6HzYyfNoqM_Ew3OGQqk9PHbv8CjKN6sR53UMNRJeFxkW2owCsR0eCvc8kL-tc5RyHWF3zWVmlOxmzDaHZo_XlA0fgEpjlMZS1ClHCBT6_ZoQRvKan0dkFfhJEdp35aK_v9DLXs46Sfs2rqfN0Fdr698gv0UbGsLdeR00W7M9qMsvXoFDBW3-GnIqsxjjepDPlv4RInMKfSeVdISp4VPWW-GjGyzCB1ooWiyZybaGul1FsdXVSibMq6qsiGUQNr08uf_In3NUPFCKNxJ2iR6A_5-TEiIIjcK6ywbI87L13PFT3oCCXiFxRPjp4f1nUUTGxLcetGzYC_eYmQD004R5M5u1epQdWen4Of1Fzn7D0sOWibSHcl_J9xSxzzVt__b9NVDWieoaGYCO3MJCDVmucfFZ1UFPhIRwsr3nUnom8mnXJocDDSPlb0EWfZhCrMgjhPt7Iqcjg-uNB9QYZNjtHASAcQlUYx5GfP6IZs47UqqLPRlzUISsc65CPyQF6sFgwPO1GNy5Q7QcCUQreMmJdBUyYEUnrKCurZkfRWx2eEJ_1efnnprtUc_Upniar-5PJxAfsZ0Mw4QRweIriRB2CW7L24yZsLR7Q8xzm0vj4KeXeuZ7ZlJJw5f65xndTNwII0jS1-VriBsnKs1SDXJc3WEiviifG8Lx-IjirXoH8Q7RtcqPpRURJApu1aIaWtvSEw5mCGjynuINufN_GEu2r71i231_58IYSK9fBpmRKCkHmTZWkjJmiyhFaG2aYI8Z5UwXEUhOZoijb10ZGgcyW6cnSzuthWfa5VzcYFOa35tE69_xZ8W2A6YKuJeJlW01oXirYxtBazyG2o3dpg-mD_BD7hgU4_ONU8SBXubtbxtCzWqNzIg5F0d0e2pc5aNaDJH3yzK5X1y1nlBZe59l3vCmpmvBfgWzI2Q1pbM_me-1g5-w6ju_waQLvR-DPuUOown_EbiCZ7Zd7BAszVlPMgAMWIJ3AljMceIj6ned8YFldZztM_RdvM1qW_KohVurd_bt3vvIBD_c7gttJzAohod61TYBtu5esXNr-sHQNYfapPp8U8J6KZjJFJVEPdrNYeGFewVFVsgRCx_WfaEyIUTaoC9d_ZTDX_nFn_GJceUANqsJYB_FSbzz7aZLj2WKGK8WKw6ujkSMOrLpspt0meqohTWcV68aIMNDhLdOGS7R53vnTUoyrfGLi2HH9QyF5sjjy_YFz1Z9B1Pcv38c9XKBxHUCMNS9ws6IZlIMaA9z8F5_2s-LSKR88Atnb82gQy-BsRdffTI1IhnLLPeisPv_dVOChCdEVHmTMKDvkiYp9GobHW9V3WBm48K2mYDjR6eW459uJP1TVjGP00-O0FZDHTcBZ9L-pq93EbdhYv1VdT-S8UHWy_zoksV-D-iOmc8DKvEHU3CJcUlEf63vcRuBRzfJdeqvw2E4J5j9tt2tkAO814kng2fZaob8XUmjF3QKevYvY8NKAevp6cpoT7DIDZttT6mEkUy1pW02thh3FMqr_EfsCI5pR84BQCr-LIRDzhudnOxHxXOJXE_zuEt1QNNSAH0eqxA6Mx7N5p3WU7dU0ULGPMtEEXz1IwiGAJ21z8Z77EOrL3vOWUnq3Y1sAPD9PBzaPC8_wezBIXQqI6Ufa6D38xPdZnkoaxMd3PRFu91s9qMoYO4OZ1WfjbQJi51T4M76y1K73eBLGwVgWRguEs8Yqr2F-ctZ-BiSEa2RfOwYcmT5uRbFzZnQCtj32JTNMSIFGQ5It5bR0nPh5BK6LjK2_kbQny6dZ9d_KrBcl15REEKM9XhZOSGWRRwAmf_4iVsy6ceqXMuYMbEGL7xnw6tmBWzuuN21_1RnxY8JS8CtzjPC4LAIRgN7VE4M6LbEcQJiaw9hVsUzLueoP-CCtjBeqQ1ylsaz6C4rOpDISATG-jAQ66FE9P0YHXQXOAip4Bf7KO-IvSvZF_dKv2_RMdAE53dlpup5oCWqPk8qAVNgZXIT6LN8MiqRDVfObQDa-uElVtX8ll7ItOUXRoXUJfxabE6oW.bDrh_KN_-hbGsWTk_0z35g"
}
chatbot = Chatbot(config)
user_session = dict()
last_session_refresh = time.time()


class ChatGPTBot(Bot):
    def reply(self, query, context=None):

        from_user_id = context['from_user_id']
        logger.info("[GPT]query={}, user_id={}, session={}".format(query, from_user_id, user_session))

        now = time.time()
        global last_session_refresh
        if now - last_session_refresh > 60 * 8:
            logger.info('[GPT]session refresh, now={}, last={}'.format(now, last_session_refresh))
            chatbot.refresh_session()
        last_session_refresh = now

        if from_user_id in user_session:
            if time.time() - user_session[from_user_id]['last_reply_time'] < 60 * 5:
                chatbot.conversation_id = user_session[from_user_id]['conversation_id']
                chatbot.parent_id = user_session[from_user_id]['parent_id']
            else:
                chatbot.reset_chat()
        else:
            chatbot.reset_chat()

        logger.info("[GPT]convId={}, parentId={}".format(chatbot.conversation_id, chatbot.parent_id))

        try:
            res = chatbot.get_chat_response(query, output="text")
            logger.info("[GPT]userId={}, res={}".format(from_user_id, res))

            user_cache = dict()
            user_cache['last_reply_time'] = time.time()
            user_cache['conversation_id'] = res['conversation_id']
            user_cache['parent_id'] = res['parent_id']
            user_session[from_user_id] = user_cache
            return res['message']
        except Exception as e:
            logger.error(e)
            return None
