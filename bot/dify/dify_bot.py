# encoding:utf-8
import io
import os
import mimetypes
import random
import threading
import json


import requests
from urllib.parse import urlparse, unquote

from bot.bot import Bot
from lib.dify.dify_client import DifyClient, ChatClient
from bot.dify.dify_session import DifySession, DifySessionManager
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from common import const, memory
from common.utils import parse_markdown_text
from common.tmp_dir import TmpDir
from config import conf

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
            if channel_type in ["wx", "wework", "gewechat"]:
                user = context["msg"].other_user_nickname if context.get("msg") else "default"
            elif channel_type in ["wechatcom_app", "wechatmp", "wechatmp_service", "wechatcom_service"]:
                user = context["msg"].other_user_id if context.get("msg") else "default"
            else:
                return Reply(ReplyType.ERROR, f"unsupported channel type: {channel_type}, now dify only support wx, wechatcom_app, wechatmp, wechatmp_service channel")
            logger.debug(f"[DIFY] dify_user={user}")
            user = user if user else "default" # 防止用户名为None，当被邀请进的群未设置群名称时用户名为None
            # FIXME: 群聊与私聊是同一个sessionid，应该区分不同的用户名, 同一个conversation_id下，只允许一个username，否则报错对话不存在
            session = self.sessions.get_session(session_id, user)
            logger.debug(f"[DIFY] session={session} query={query}")

            reply, err = self._reply(query, session, context)
            if err != None:
                error_msg = conf().get("error_reply", "我暂时遇到了一些问题，请您稍后重试~")
                reply = Reply(ReplyType.TEXT, error_msg)
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    # TODO: delete this function
    def _get_payload(self, query, session: DifySession, response_mode):
        return {
            'inputs': {},
            "query": query,
            "response_mode": response_mode,
            "conversation_id": session.get_conversation_id(),
            "user": session.get_user()
        }

    def _get_dify_conf(self, context: Context, key, default=None):
        return context.get(key, conf().get(key, default))

    def _reply(self, query: str, session: DifySession, context: Context):
        try:
            session.count_user_message() # 限制一个conversation中消息数，防止conversation过长
            dify_app_type = self._get_dify_conf(context, "dify_app_type", 'chatbot')
            if dify_app_type == 'chatbot':
                return self._handle_chatbot(query, session, context)
            elif dify_app_type == 'agent':
                return self._handle_agent(query, session, context)
            elif dify_app_type == 'workflow':
                return self._handle_workflow(query, session, context)
            else:
                return None, "dify_app_type must be agent, chatbot or workflow"

        except Exception as e:
            error_info = f"[DIFY] Exception: {e}"
            logger.exception(error_info)
            return None, error_info

    def _handle_chatbot(self, query: str, session: DifySession, context: Context):
        api_key = self._get_dify_conf(context, "dify_api_key", '')
        api_base = self._get_dify_conf(context, "dify_api_base", "https://api.dify.ai/v1")
        chat_client = ChatClient(api_key, api_base)
        response_mode = 'blocking'
        payload = self._get_payload(query, session, response_mode)
        files = self._get_upload_files(session, context)
        response = chat_client.create_chat_message(
            inputs=payload['inputs'],
            query=payload['query'],
            user=payload['user'],
            response_mode=payload['response_mode'],
            conversation_id=payload['conversation_id'],
            files=files
        )

        if response.status_code != 200:
            error_info = f"[DIFY] payload={payload} response text={response.text} status_code={response.status_code}"
            logger.warn(error_info)
            return None, error_info

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
        logger.debug("[DIFY] usage {}".format(rsp_data.get('metadata', {}).get('usage', 0)))

        answer = rsp_data['answer']
        parsed_content = parse_markdown_text(answer)

        # {"answer": "![image](/files/tools/dbf9cd7c-2110-4383-9ba8-50d9fd1a4815.png?timestamp=1713970391&nonce=0d5badf2e39466042113a4ba9fd9bf83&sign=OVmdCxCEuEYwc9add3YNFFdUpn4VdFKgl84Cg54iLnU=)"}
        at_prefix = ""
        channel = context.get("channel")
        is_group = context.get("isgroup", False)
        if is_group:
            at_prefix = "@" + context["msg"].actual_user_nickname + "\n"
        for item in parsed_content[:-1]:
            reply = None
            if item['type'] == 'text':
                content = at_prefix + item['content']
                reply = Reply(ReplyType.TEXT, content)
            elif item['type'] == 'image':
                image_url = self._fill_file_base_url(item['content'])
                image = self._download_image(image_url)
                if image:
                    reply = Reply(ReplyType.IMAGE, image)
                else:
                    reply = Reply(ReplyType.TEXT, f"图片链接：{image_url}")
            elif item['type'] == 'file':
                file_url = self._fill_file_base_url(item['content'])
                file_path = self._download_file(file_url)
                if file_path:
                    reply = Reply(ReplyType.FILE, file_path)
                else:
                    reply = Reply(ReplyType.TEXT, f"文件链接：{file_url}")
            logger.debug(f"[DIFY] reply={reply}")
            if reply and channel:
                channel.send(reply, context)
        # parsed_content 没有数据时，直接不回复
        if not parsed_content:
            return None, None
        final_item = parsed_content[-1]
        final_reply = None
        if final_item['type'] == 'text':
            content = final_item['content']
            if is_group:
                at_prefix = "@" + context["msg"].actual_user_nickname + "\n"
                content = at_prefix + content
            final_reply = Reply(ReplyType.TEXT, final_item['content'])
        elif final_item['type'] == 'image':
            image_url = self._fill_file_base_url(final_item['content'])
            image = self._download_image(image_url)
            if image:
                final_reply = Reply(ReplyType.IMAGE, image)
            else:
                final_reply = Reply(ReplyType.TEXT, f"图片链接：{image_url}")
        elif final_item['type'] == 'file':
            file_url = self._fill_file_base_url(final_item['content'])
            file_path = self._download_file(file_url)
            if file_path:
                final_reply = Reply(ReplyType.FILE, file_path)
            else:
                final_reply = Reply(ReplyType.TEXT, f"文件链接：{file_url}")

        # 设置dify conversation_id, 依靠dify管理上下文
        if session.get_conversation_id() == '':
            session.set_conversation_id(rsp_data['conversation_id'])

        return final_reply, None

    def _download_file(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            parsed_url = urlparse(url)
            logger.debug(f"Downloading file from {url}")
            url_path = unquote(parsed_url.path)
            # 从路径中提取文件名
            file_name = url_path.split('/')[-1]
            logger.debug(f"Saving file as {file_name}")
            file_path = os.path.join(TmpDir().path(), file_name)
            with open(file_path, 'wb') as file:
                file.write(response.content)
            return file_path
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
        return None

    def _download_image(self, url):
        try:
            pic_res = requests.get(url, stream=True)
            pic_res.raise_for_status()
            image_storage = io.BytesIO()
            size = 0
            for block in pic_res.iter_content(1024):
                size += len(block)
                image_storage.write(block)
            logger.debug(f"[WX] download image success, size={size}, img_url={url}")
            image_storage.seek(0)
            return image_storage
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
        return None

    def _handle_agent(self, query: str, session: DifySession, context: Context):
        api_key = self._get_dify_conf(context, "dify_api_key", '')
        api_base = self._get_dify_conf(context, "dify_api_base", "https://api.dify.ai/v1")
        chat_client = ChatClient(api_key, api_base)
        response_mode = 'streaming'
        payload = self._get_payload(query, session, response_mode)
        files = self._get_upload_files(session, context)
        response = chat_client.create_chat_message(
            inputs=payload['inputs'],
            query=payload['query'],
            user= payload['user'],
            response_mode=payload['response_mode'],
            conversation_id=payload['conversation_id'],
            files=files
        )

        if response.status_code != 200:
            error_info = f"[DIFY] payload={payload} response text={response.text} status_code={response.status_code}"
            logger.warn(error_info)
            return None, error_info
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
                url = self._fill_file_base_url(msg['content']['url'])
                reply = Reply(ReplyType.IMAGE_URL, url)
                thread = threading.Thread(target=channel.send, args=(reply, context))
                thread.start()
        final_msg = msgs[-1]
        reply = None
        if final_msg['type'] == 'agent_message':
            reply = Reply(ReplyType.TEXT, final_msg['content'])
        elif final_msg['type'] == 'message_file':
            url = self._fill_file_base_url(final_msg['content']['url'])
            reply = Reply(ReplyType.IMAGE_URL, url)
        # 设置dify conversation_id, 依靠dify管理上下文
        if session.get_conversation_id() == '':
            session.set_conversation_id(conversation_id)
        return reply, None

    def _handle_workflow(self, query: str, session: DifySession, context: Context):
        payload = self._get_workflow_payload(query, session)
        api_key = self._get_dify_conf(context, "dify_api_key", '')
        api_base = self._get_dify_conf(context, "dify_api_base", "https://api.dify.ai/v1")
        dify_client = DifyClient(api_key, api_base)
        response = dify_client._send_request("POST", "/workflows/run", json=payload)
        if response.status_code != 200:
            error_info = f"[DIFY] payload={payload} response text={response.text} status_code={response.status_code}"
            logger.warn(error_info)
            return None, error_info

        #  {
        #      "log_id": "djflajgkldjgd",
        #      "task_id": "9da23599-e713-473b-982c-4328d4f5c78a",
        #      "data": {
        #          "id": "fdlsjfjejkghjda",
        #          "workflow_id": "fldjaslkfjlsda",
        #          "status": "succeeded",
        #          "outputs": {
        #          "text": "Nice to meet you."
        #          },
        #          "error": null,
        #          "elapsed_time": 0.875,
        #          "total_tokens": 3562,
        #          "total_steps": 8,
        #          "created_at": 1705407629,
        #          "finished_at": 1727807631
        #      }
        #  }

        rsp_data = response.json()
        if 'data' not in rsp_data or 'outputs' not in rsp_data['data'] or 'text' not in rsp_data['data']['outputs']:
            error_info = f"[DIFY] Unexpected response format: {rsp_data}"
            logger.warn(error_info)
            return None, error_info
        reply = Reply(ReplyType.TEXT, rsp_data['data']['outputs']['text'])
        return reply, None

    def _get_upload_files(self, session: DifySession, context: Context):
        session_id = session.get_session_id()
        img_cache = memory.USER_IMAGE_CACHE.get(session_id)
        if not img_cache or not self._get_dify_conf(context, "image_recognition", False):
            return None
        # 清理图片缓存
        memory.USER_IMAGE_CACHE[session_id] = None
        api_key = self._get_dify_conf(context, "dify_api_key", '')
        api_base = self._get_dify_conf(context, "dify_api_base", "https://api.dify.ai/v1")
        dify_client = DifyClient(api_key, api_base)
        msg = img_cache.get("msg")
        path = img_cache.get("path")
        msg.prepare()

        with open(path, 'rb') as file:
            file_name = os.path.basename(path)
            file_type, _ = mimetypes.guess_type(file_name)
            files = {
                'file': (file_name, file, file_type)
            }
            response = dify_client.file_upload(user=session.get_user(), files=files)

        if response.status_code != 200 and response.status_code != 201:
            error_info = f"[DIFY] response text={response.text} status_code={response.status_code} when upload file"
            logger.warn(error_info)
            return None, error_info
        # {
        #     'id': 'f508165a-10dc-4256-a7be-480301e630e6',
        #     'name': '0.png',
        #     'size': 17023,
        #     'extension': 'png',
        #     'mime_type': 'image/png',
        #     'created_by': '0d501495-cfd4-4dd4-a78b-a15ed4ed77d1',
        #     'created_at': 1722781568
        # }
        file_upload_data = response.json()
        logger.debug("[DIFY] upload file {}".format(file_upload_data))
        return [
            {
                "type": "image",
                "transfer_method": "local_file",
                "upload_file_id": file_upload_data['id']
            }
        ]

    def _fill_file_base_url(self, url: str):
        if url.startswith("https://") or url.startswith("http://"):
            return url
        # 补全文件base url, 默认使用去掉"/v1"的dify api base url
        return self._get_file_base_url() + url

    def _get_file_base_url(self) -> str:
        api_base = conf().get("dify_api_base", "https://api.dify.ai/v1")
        return api_base.replace("/v1", "")

    def _get_workflow_payload(self, query, session: DifySession):
        return {
            'inputs': {
                "query": query
            },
            "response_mode": "blocking",
            "user": session.get_user()
        }

    def _parse_sse_event(self, event_str):
        """
        Parses a single SSE event string and returns a dictionary of its data.
        """
        event_prefix = "data: "
        if not event_str.startswith(event_prefix):
            return None
        trimmed_event_str = event_str[len(event_prefix):]

        # Check if trimmed_event_str is not empty and is a valid JSON string
        if trimmed_event_str:
            try:
                event = json.loads(trimmed_event_str)
                return event
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from SSE event: {trimmed_event_str}")
                return None
        else:
            logger.warn("Received an empty SSE event.")
            return None

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
