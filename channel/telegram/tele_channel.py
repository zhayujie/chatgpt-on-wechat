# encoding:utf-8


import asyncio

from common.log import logger
from channel.channel import Channel
from telegram import Bot
from telegram.error import Forbidden, NetworkError
from config import conf
from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)
from bridge.context import *
from bridge.reply import *




class TelegramChannel(Channel):
    def __init__(self):
        pass

    def startup(self):
        logger.info("创建telegram")
        application = Application.builder().token(conf().get("telegramToken")).build()
        application.add_handler(MessageHandler(filters.COMMAND, self._cmd_handler))
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def _echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(update.message.text)        

    async def _cmd_handler(self,update:Update,context:ContextTypes.DEFAULT_TYPE):
        msg = update.message
        logger.info("cmd input:"+msg.text)
        if msg.text.startswith("/chat"):
            openai_ctx =Context()
            openai_ctx.type = ContextType.TEXT
            openai_ctx['session_id'] = msg.from_user.id
            prompt = msg.text[5:]
            openai_ctx.content = prompt
            reply_str = super().build_reply_content(prompt, openai_ctx).content

            await update.message.reply_text(reply_str)
        else:
            await update.message.reply_text("这火我不传")  
