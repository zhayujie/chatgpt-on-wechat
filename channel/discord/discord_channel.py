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
        self.bot = commands.Bot(command_prefix='>', intents=self.intents, ssl=context)
        self.bot.add_listener(self.on_ready)


    def startup(self):
        self.bot.add_listener(self.on_message)
        self.bot.run(self.token)

    async def on_ready(self):
        print('Bot is online user:', self.bot.user)
        if self.voice_enabled == False: 
            await self.bot.remove_cog("Music")

    async def on_message(self, message):
        """
        listen for message event
        """
        await self.bot.wait_until_ready()
        # print('discord message:', message)
        if message.author == self.bot.user:
            print('can not be bot user')
            return
        
        prompt = message.content;
        if not prompt:
            print('no prompt author:', message.author)
            return
        # print('prompt:', prompt)
        context = Context()
        context.type = ContextType.TEXT
        context['session_id'] = "User"
        context.content = prompt
        response = super().build_reply_content(prompt, context).content
        # print('response', response)
        await message.channel.send(response)


