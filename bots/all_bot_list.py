"""Functionality for loading bots."""

from bots.catgirl_bot.base import CatGirlBot
from bots.chat_bot.base import ChatBot
from bots.qa_bot.base import QABot


BOT_TO_CLASS = {
    "qa-bot": QABot,
    "chat-bot": ChatBot,
    "catgirl-bot": CatGirlBot,
    "default": QABot,
}
