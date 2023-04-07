# encoding:utf-8

"""
discord channel
Python discord - https://github.com/Rapptz/discord.py.git
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
        self.discord_channel_name = config.get('discord_channel_name')
        self.discord_channel_session = config.get('discord_channel_session', 'author')
        self.cmd_clear_session = config.get('cmd_clear_session')
        self.cmd_clear_all_session = config.get('cmd_clear_all_session')
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.guilds = True
        self.intents.members = True
        self.intents.messages = True
        self.intents.voice_states = True
        self.voice_enabled = config.get('voice_enabled')
        context = ssl.create_default_context()
        context.load_verify_locations(config.get('certificate_file'))
        self.bot = commands.Bot(command_prefix='!', intents=self.intents, ssl=context)
        self.bot.add_listener(self.on_ready)

        logger.debug('cmd_clear_session %s', self.cmd_clear_session)
        logger.debug('cmd_clear_all_session %s', self.cmd_clear_all_session)

    def startup(self):
        self.bot.add_listener(self.on_message)
        self.bot.add_listener(self.on_guild_channel_delete)
        self.bot.add_listener(self.on_guild_channel_create)
        self.bot.add_listener(self.on_private_channel_delete)
        self.bot.add_listener(self.on_private_channel_create)
        self.bot.add_listener(self.on_channel_delete)
        self.bot.add_listener(self.on_channel_create)
        self.bot.add_listener(self.on_thread_delete)
        self.bot.add_listener(self.on_thread_create)
        self.bot.run(self.token)

    async def on_ready(self):
        logger.info('Bot is online user:{}'.format(self.bot.user))
        if self.voice_enabled == False: 
            logger.debug('disable music')
            await self.bot.remove_cog("Music")
    
    async def join(self, ctx):
        logger.debug('join %s', repr(ctx))
        channel = ctx.author.voice.channel
        await channel.connect()

    async def _do_on_channel_delete(self, channel):
        if not self.discord_channel_name or channel.name != self.discord_channel_name:
            logger.debug('skip _do_on_channel_delete %s', channel.name)
            return
        
        context = Context()
        context.type = ContextType.TEXT
        context['session_id'] = channel.name
        context.content = self.cmd_clear_all_session
        response = super().build_reply_content(self.cmd_clear_all_session, context).content
        logger.debug('_do_on_channel_delete %s %s', channel.name, response)

    async def on_guild_channel_delete(self, channel):
        logger.debug('on_guild_channel_delete %s', repr(channel))
        await self._do_on_channel_delete(channel)
    
    async def on_guild_channel_create(self, channel):
        logger.debug('on_guild_channel_create %s', repr(channel))

    async def on_private_channel_delete(self, channel):
        logger.debug('on_channel_delete %s', repr(channel))
        await self._do_on_channel_delete(channel)
    
    async def on_private_channel_create(self, channel):
        logger.debug('on_channel_create %s', repr(channel))

    async def on_channel_delete(self, channel):
        logger.debug('on_channel_delete %s', repr(channel))
    
    async def on_channel_create(self, channel):
        logger.debug('on_channel_create %s', repr(channel))

    async def on_thread_delete(self, thread):
        if self.discord_channel_session != 'thread':
            logger.debug('skip on_thread_delete %s', thread.id)
            return
        
        context = Context()
        context.type = ContextType.TEXT
        context['session_id'] = thread.id
        context.content = self.cmd_clear_session
        response = super().build_reply_content(self.cmd_clear_session, context).content
        logger.debug('on_thread_delete %s %s', thread.id, response)

    async def on_thread_create(self, thread):
        logger.debug('on_thread_create %s', thread.id) 

    async def on_message(self, message):
        """
        listen for message event
        """
        await self.bot.wait_until_ready()
        if not self.check_message(message):
            return
 
        prompt = message.content.strip();
        logger.debug('author: %s', message.author)
        logger.debug('prompt: %s', prompt)

        context = Context()
        context.type = ContextType.TEXT
        if self.discord_channel_session == 'thread' and isinstance(message.channel, discord.Thread):
            logger.debug('on_message thread id %s', message.channel.id)
            context['session_id'] = message.channel.id
        else:
            logger.debug('on_message author %s', message.author)
            context['session_id'] = message.author
        context.content = prompt
        response = super().build_reply_content(prompt, context).content
        await message.channel.send(response)


    def check_message(self, message):
        if message.author == self.bot.user:
            logger.debug('can not be bot user')
            return False
        
        prompt = message.content.strip();
        if not prompt:
            logger.debug('no prompt author: %s', message.author)
            return False
   
        if self.discord_channel_name:
            if isinstance(message.channel, discord.Thread) and message.channel.parent.name == self.discord_channel_name:
                return True
            if not isinstance(message.channel, discord.Thread) and self.discord_channel_session != 'thread' and message.channel.name == self.discord_channel_name:
                return True
            
            logger.debug("The accessed channel does not meet the discord channel configuration conditions.")
            return False
        else:
            return True