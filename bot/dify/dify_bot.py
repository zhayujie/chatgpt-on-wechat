# encoding:utf-8
import json
import threading

import requests

from bot.bot import Bot
from bot.openai.open_ai_image import OpenAIImage
from bot.ali.ali_qwen_session import AliQwenSession
from bot.session_manager import SessionManager
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from common import const
from config import conf, load_config

class DifyBot(Bot, OpenAIImage):
    def __init__(self):
        super().__init__()
        # 复用千问的Session
        self.sessions = SessionManager(AliQwenSession, model=conf().get("model", const.DIFY))

    def reply(self, query, context: Context=None):
        # acquire reply content
        if context.type == ContextType.TEXT or context.type == ContextType.IMAGE_CREATE:
            if context.type == ContextType.IMAGE_CREATE:
                query = conf().get('image_create_prefix', ['画'])[0] + query
            logger.info("[DIFY] query={}".format(query))
            session_id = context["session_id"]
            reply = None
            clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])
            if query in clear_memory_commands:
                self.sessions.clear_session(session_id)
                reply = Reply(ReplyType.INFO, "记忆已清除")
            elif query == "#清除所有":
                self.sessions.clear_all_session()
                reply = Reply(ReplyType.INFO, "所有人记忆已清除")
            elif query == "#更新配置":
                load_config()
                reply = Reply(ReplyType.INFO, "配置已更新")
            if reply:
                return reply
            session = self.sessions.session_query(query, session_id)
            logger.debug("[DIFY] session query={}".format(session.messages))

            reply, err = self._reply(session, context)
            if err != None:
                reply = Reply(ReplyType.ERROR, err)
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def _get_api_base_url(self):
        return conf().get("dify_api_base", "https://api.dify.ai/v1")

    def _get_headers(self):
        return {
            'Authorization': f"Bearer {conf().get('dify_api_key', '')}"
        }

    def _get_payload(self, session, response_mode):
        return {
            'inputs': {},
            "query": session['query'],
            "response_mode": response_mode,
            "conversation_id": session['conversation_id'],
            "user": session['user']
        }

    def _reply(self, session: AliQwenSession, context: Context):
        try:
            base_url = self._get_api_base_url()
            chat_url = f'{base_url}/chat-messages'
            headers = self._get_headers()
            is_dify_agent = conf().get('dify_agent', True)
            response_mode = 'streaming' if is_dify_agent else 'blocking'
            dify_session = {'user': session.session_id, 'conversation_id': '', 'query': session.messages[-1]['content']}
            payload = self._get_payload(dify_session, response_mode)
            response = requests.post(chat_url, headers=headers, json=payload, stream=is_dify_agent)
            if response.status_code != 200:
                error_info = f"[DIFY] response text={response.text} status_code={response.status_code}"
                logger.warn(error_info)
                return None, error_info

            # {
            #   'event': 'message', 
            #   'task_id': 'xxxx', 
            #   'id': 'xxx', 
            #   'answer': 'xxx',
            #   'metadata': {}, 
            #   'created_at': 1703326868, 
            #   'conversation_id': '4ba26448-a003-478d-b364-e918e37e42bb'
            # }
            if is_dify_agent:
                msgs = self._handle_sse_response(response)
                channel = context.get("channel")
                is_group = context.get("isgroup", False)
                for msg in msgs[:-1]:
                    if msg['type'] == 'agent_message':
                        if is_group:
                            at_prefix = "@" + context["msg"].actual_user_nickname + "\n"
                            msg['content'] = at_prefix + msg['content']
                        reply = Reply(ReplyType.TEXT, msg['content'])
                        channel.send(reply, context)
                    elif msg['type'] == 'message_file':
                        reply = Reply(ReplyType.IMAGE_URL, msg['content']['url'])
                        thread = threading.Thread(target=channel.send, args=(reply, context))
                        thread.start()
                final_msg = msgs[-1]
                reply = None
                if final_msg['type'] == 'agent_message':
                    reply = Reply(ReplyType.TEXT, final_msg['content'])
                elif final_msg['type'] == 'message_file':
                    reply = Reply(ReplyType.IMAGE_URL, final_msg['content']['url'])
                return reply, None
            else:
                rsp_data = response.json()
                logger.debug("[DIFY] usage ".format(rsp_data['metadata']['usage']))
                reply = Reply(ReplyType.TEXT, rsp_data['answer'])
                return reply, None
        except Exception as e:
            error_info = f"[DIFY] Exception: {e}"
            logger.exception(error_info)
            return None, error_info

    def _parse_sse_event(self, event_str):
        """
        Parses a single SSE event string and returns a dictionary of its data.
        """
        event_prefix = "data: "
        if not event_str.startswith(event_prefix):
            return None
        trimed_event_str = event_str[len(event_prefix):]
        event = json.loads(trimed_event_str)
        return event

    # TODO: 异步返回events
    def _handle_sse_response(self, response: requests.Response):
        events = []
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                event = self._parse_sse_event(decoded_line)
                if event:
                    events.append(event)

        merged_message = []
        accumulated_agent_message = ''
        for event in events:
            event_name = event['event']
            if event_name == 'agent_message':
                accumulated_agent_message += event['answer']
            elif event_name == 'agent_thought':
                self._append_agent_message(accumulated_agent_message, merged_message)
                accumulated_agent_message = ''
                logger.debug("[DIFY] agent_thought: {}".format(event))
            elif event_name == 'message_file':
                self._append_agent_message(accumulated_agent_message, merged_message)
                accumulated_agent_message = ''
                self._append_message_file(event, merged_message)
            elif event_name == 'message_replace':
                # TODO: handle message_replace
                pass
            elif event_name == 'error':
                logger.error("[DIFY] error: {}".format(event))
                raise Exception(event)
            elif event_name == 'message_end':
                self._append_agent_message(accumulated_agent_message, merged_message)
                logger.debug("[DIFY] message_end usage: {}".format(event['metadata']['usage']))
                break
            else:
                logger.warn("[DIFY] unknown event: {}".format(event))

        return merged_message

    def _append_agent_message(self, accumulated_agent_message,  merged_message):
        if accumulated_agent_message:
            merged_message.append({
                'type': 'agent_message',
                'content': accumulated_agent_message,
            })
    def _append_message_file(self, event: dict, merged_message: list):
        if event.get('type') != 'image':
            logger.warn("[DIFY] unsupported message file type: {}".format(event))
        merged_message.append({
            'type': 'message_file',
            'content': event,
        })