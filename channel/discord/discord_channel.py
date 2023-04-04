# encoding:utf-8

"""
discord channel
Python Wechaty - https://github.com/wechaty/python-wechaty
"""
import os
import time
import asyncio
from typing import Optional, Union
from bridge.context import Context, ContextType
from channel.channel import Channel
from common.log import logger
from common.tmp_dir import TmpDir
from config import conf
from voice.audio_convert import sil_to_wav, mp3_to_sil
import ssl
import discord
from discord.ext import commands

class DiscordChannel(Channel):

    def __init__(self):
        config = conf()
        self.token = config.get('discord_app_token')
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.voice_enabled = config.get('voice_enabled')
        context = ssl.create_default_context()
        context.load_verify_locations(config.get('certificate_file'))
        self.bot = commands.Bot(command_prefix='!', intents=self.intents, ssl=context)
        self.bot.add_listener(self.on_ready)


    def startup(self):
        self.bot.add_listener(self.on_message)
        self.bot.run(self.token)

    async def on_ready(self):
        logger.info('Bot is online user:{}'.format(self.bot.user))
        if self.voice_enabled == False: 
            logger.debug('disable music')
            await self.bot.remove_cog("Music")
    
    async def join(ctx):
        logger.debug('join %s', repr(ctx))
        channel = ctx.author.voice.channel
        await channel.connect()

    async def on_message(self, message):
        """
        listen for message event
        """
        await self.bot.wait_until_ready()
        logger.debug('discord message: %s', repr(message))
        if message.author == self.bot.user:
            print('can not be bot user')
            return
        
        prompt = message.content;
        if not prompt:
            logger.debug('no prompt author: %s', message.author)
            return
        logger.debug('author: %s', message.author)
        logger.debug('prompt: %s', prompt)

        context = Context()
        context.type = ContextType.TEXT
        context['session_id'] = message.author
        context.content = prompt
        response = super().build_reply_content(prompt, context).content
        # print('response', response)
        await message.channel.send(response)


