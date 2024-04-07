# encoding:utf-8
import json
import threading

import requests

from bot.bot import Bot
from bot.dify.dify_session import DifySession, DifySessionManager
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from common import const
from config import conf, load_config

class DifyBot(Bot):
    def __init__(self):
        super().__init__()
        self.sessions = DifySessionManager(DifySession, model=conf().get("model", const.DIFY))

    def reply(self, query, context: Context=None):
        # acquire reply content
        if context.type == ContextType.TEXT or context.type == ContextType.IMAGE_CREATE:
            if context.type == ContextType.IMAGE_CREATE:
                query = conf().get('image_create_prefix', ['画'])[0] + query
            logger.info("[DIFY] query={}".format(query))
            session_id = context["session_id"]
            # TODO: 适配除微信以外的其他channel
            channel_type = conf().get("channel_type", "wx")
            user = None
            if channel_type == "wx":
                user = context["msg"].other_user_nickname
            elif channel_type in ["wechatcom_app", "wechatmp", "wechatmp_service"]:
                user = context["msg"].other_user_id
            else:
                return Reply(ReplyType.ERROR, f"unsupported channel type: {channel_type}, now dify only support wx, wechatcom_app, wechatmp, wechatmp_service channel")
            logger.debug(f"[DIFY] dify_user={user}")
            user = user if user else "default" # 防止用户名为None，当被邀请进的群未设置群名称时用户名为None
            session = self.sessions.get_session(session_id, user)
            logger.debug(f"[DIFY] session={session} query={query}")

            reply, err = self._reply(query, session, context)
            if err != None:
                reply = Reply(ReplyType.TEXT, "我暂时遇到了一些问题，请您稍后重试~")
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

    def _get_payload(self, query, session: DifySession, response_mode):
        return {
            'inputs': {},
            "query": query,
            "response_mode": response_mode,
            "conversation_id": session.get_conversation_id(),
            "user": session.get_user()
        }

    def _reply(self, query: str, session: DifySession, context: Context):
        try:
            session.count_user_message() # 限制一个conversation中消息数，防止conversation过长
            base_url = self._get_api_base_url()
            chat_url = f'{base_url}/chat-messages'
            headers = self._get_headers()
            is_dify_agent = conf().get('dify_agent', True)
            response_mode = 'streaming' if is_dify_agent else 'blocking'
            payload = self._get_payload(query, session, response_mode)
            response = requests.post(chat_url, headers=headers, json=payload, stream=is_dify_agent)
            if response.status_code != 200:
                error_info = f"[DIFY] response text={response.text} status_code={response.status_code}"
                logger.warn(error_info)
                return None, error_info

            if is_dify_agent:
                # response:
                # data: {"event": "agent_thought", "id": "8dcf3648-fbad-407a-85dd-73a6f43aeb9f", "task_id": "9cf1ddd7-f94b-459b-b942-b77b26c59e9b", "message_id": "1fb10045-55fd-4040-99e6-d048d07cbad3", "position": 1, "thought": "", "observation": "", "tool": "", "tool_input": "", "created_at": 1705639511, "message_files": [], "conversation_id": "c216c595-2d89-438c-b33c-aae5ddddd142"}
                # data: {"event": "agent_thought", "id": "8dcf3648-fbad-407a-85dd-73a6f43aeb9f", "task_id": "9cf1ddd7-f94b-459b-b942-b77b26c59e9b", "message_id": "1fb10045-55fd-4040-99e6-d048d07cbad3", "position": 1, "thought": "", "observation": "", "tool": "dalle3", "tool_input": "{\"dalle3\": {\"prompt\": \"cute Japanese anime girl with white hair, blue eyes, bunny girl suit\"}}", "created_at": 1705639511, "message_files": [], "conversation_id": "c216c595-2d89-438c-b33c-aae5ddddd142"}
                # data: {"event": "agent_message", "id": "1fb10045-55fd-4040-99e6-d048d07cbad3", "task_id": "9cf1ddd7-f94b-459b-b942-b77b26c59e9b", "message_id": "1fb10045-55fd-4040-99e6-d048d07cbad3", "answer": "I have created an image of a cute Japanese", "created_at": 1705639511, "conversation_id": "c216c595-2d89-438c-b33c-aae5ddddd142"}
                # data: {"event": "message_end", "task_id": "9cf1ddd7-f94b-459b-b942-b77b26c59e9b", "id": "1fb10045-55fd-4040-99e6-d048d07cbad3", "message_id": "1fb10045-55fd-4040-99e6-d048d07cbad3", "conversation_id": "c216c595-2d89-438c-b33c-aae5ddddd142", "metadata": {"usage": {"prompt_tokens": 305, "prompt_unit_price": "0.001", "prompt_price_unit": "0.001", "prompt_price": "0.0003050", "completion_tokens": 97, "completion_unit_price": "0.002", "completion_price_unit": "0.001", "completion_price": "0.0001940", "total_tokens": 184, "total_price": "0.0002290", "currency": "USD", "latency": 1.771092874929309}}}
                msgs, conversation_id = self._handle_sse_response(response)
                channel = context.get("channel")
                # TODO: 适配除微信以外的其他channel
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
                # 设置dify conversation_id, 依靠dify管理上下文
                if session.get_conversation_id() == '':
                    session.set_conversation_id(conversation_id)
                return reply, None
            else:
                # response: 
                # {
                #     "event": "message",
                #     "message_id": "9da23599-e713-473b-982c-4328d4f5c78a",
                #     "conversation_id": "45701982-8118-4bc5-8e9b-64562b4555f2",
                #     "mode": "chat",
                #     "answer": "xxx",
                #     "metadata": {
                #         "usage": {
                #         },
                #         "retriever_resources": []
                #     },
                #     "created_at": 1705407629
                # }
                rsp_data = response.json()
                logger.debug("[DIFY] usage ".format(rsp_data['metadata']['usage']))
                reply = Reply(ReplyType.TEXT, rsp_data['answer'])
                # 设置dify conversation_id, 依靠dify管理上下文
                if session.get_conversation_id() == '':
                    session.set_conversation_id(rsp_data['conversation_id'])
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
        conversation_id = None
        for event in events:
            event_name = event['event']
            if event_name == 'agent_message' or event_name == 'message':
                accumulated_agent_message += event['answer']
                logger.debug("[DIFY] accumulated_agent_message: {}".format(accumulated_agent_message))
                # 保存conversation_id
                if not conversation_id:
                    conversation_id = event['conversation_id']
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
        
        if not conversation_id:
            raise Exception("conversation_id not found")
        
        return merged_message, conversation_id

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
