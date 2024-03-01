"""
Main.py
"""
from __future__ import annotations

from .chathub import *
from .constants import APP_ID, PLUGINS
from .conversation import *
from .request import *
from .utils.exception.exception_message import add_plugin_failed_message
from .utils.exception.exceptions import LimitExceeded, PluginError


class Chatbot:
    """
    Combines everything to make it seamless
    """

    def __init__(
            self,
            proxy: str | None = None,
            cookies: list[dict] | None = None
    ) -> None:
        self.proxy: str | None = proxy
        self.chat_hub: ChatHub = ChatHub(
            Conversation(self.proxy, cookies=cookies),
            proxy=self.proxy,
            cookies=cookies,
        )

    async def add_plugins(self, cookies: list[dict], mode: str, conversation_id: str,
                          plugin_ids: Union[None, List[str]] = None) -> None:
        cookies_dict = {}
        if cookies is not None:
            for cookie in cookies:
                cookies_dict[cookie["name"]] = cookie["value"]

        async with httpx.AsyncClient(
                proxies=self.proxy,
                timeout=30,
                headers=HEADERS_INIT_CONVER,
                cookies=cookies_dict
        ) as client:
            if plugin_ids is not None:
                for plugin_id in plugin_ids:
                    if mode == "Bing":
                        response = await client.post(
                            f"https://www.bing.com/codex/plugins/conversation/add"
                            f"?conversationId={conversation_id}"
                            f"&appid={APP_ID}&pluginId={plugin_id}"
                        )
                    else:
                        response = await client.post(
                            f"https://copilot.microsoft.com/turing/plugins/conversation/add"
                            f"?conversationId={conversation_id}"
                            f"&appid={APP_ID}&pluginId={plugin_id}"
                        )
                    if response.status_code != 200:
                        raise PluginError(add_plugin_failed_message)

    @staticmethod
    async def create(
            proxy: str | None = None,
            cookies: list[dict] | None = None,
            mode: str | None = None,
            plugin_ids: Union[None, List[str]] = None
    ) -> Chatbot:
        self = Chatbot.__new__(Chatbot)
        self.proxy = proxy
        self.mode = mode
        conversation = await Conversation.create(self.proxy, cookies=cookies, mode=mode)
        if plugin_ids is not None:
            new_plugin_list = [PLUGINS.get(plugin, plugin) for plugin in plugin_ids]
            await self.add_plugins(cookies, mode, conversation.struct["conversationId"], new_plugin_list)
        self.chat_hub = ChatHub(
            conversation,
            proxy=self.proxy,
            cookies=cookies,
            mode=mode
        )
        return self

    async def ask(
            self,
            prompt: str,
            wss_link: str = "wss://sydney.bing.com/sydney/ChatHub",
            conversation_style: CONVERSATION_STYLE_TYPE = None,
            webpage_context: str | None = None,
            search_result: bool = False,
            locale: str = guess_locale(),
            simplify_response: bool = False,
            attachment: dict[str, str] = None,
            remove_options: list = None,
            add_options: list = None
    ):
        """
        Ask a question to the bot
        :param prompt: The prompt to ask Bing
        :param wss_link: The link to the Bing web service
        :param conversation_style: The style of the Bing chat
        :param webpage_context: U don't need use this param in normal use
        :param search_result: Search web True or False
        :param locale: Bing service locale
        :param simplify_response: Simplify response True or False
        :param attachment: Send image
            attachment example:
                For url using
                attachment={"image_url": r"<image_url>"})
                For local file using
                attachment={"filename": r"<file_path>"})
                For base64 image using
                attachment={"base64_image": r"<base64_image_str>"})
        :param remove_options remove options from Style
        :param add_options add options to Style
        """
        async for final, response in self.chat_hub.ask_stream(
                prompt=prompt,
                conversation_style=conversation_style,
                wss_link=wss_link,
                webpage_context=webpage_context,
                search_result=search_result,
                locale=locale,
                attachment=attachment,
                remove_options=remove_options,
                add_options=add_options
        ):
            if final:
                if not simplify_response:
                    return response
                messages_left = (response.get("item").get("throttling").get("maxNumUserMessagesInConversation")
                                 - response.get("item").get("throttling").get(
                            "numUserMessagesInConversation",
                            0,
                        ))
                if messages_left == 0:
                    raise LimitExceeded("Max messages reached")
                message = {}
                for msg in reversed(response.get("item").get("messages")):
                    if msg.get("author") == "bot":
                        old_message = message.get("text")
                        if old_message:
                            old_message = old_message + " \n "
                        else:
                            old_message = ""
                        message.update({
                            "author": "bot",
                            "text": old_message + msg.get("text", "")
                        })
                if not message:
                    raise NoResultsFound("No message found")
                image_create_text = ""
                suggestions = []
                source_keys = []
                source_values = []
                for detail in reversed(response.get("item").get("messages")):
                    suggestion_responses = detail.get("suggestedResponses", {})
                    source_attr = detail.get("sourceAttributions", {})
                    if suggestion_responses:
                        for suggestion in suggestion_responses:
                            suggestions.append(suggestion.get("text"))
                    if source_attr:
                        if isinstance(source_attr, dict):
                            for key, value in source_attr.items():
                                source_keys.append(key)
                                source_values.append(value)
                        if isinstance(source_attr, list):
                            for source_dict in source_attr:
                                if isinstance(source_dict, dict):
                                    source_keys.append(source_dict.get("providerDisplayName", ""))
                                    source_values.append(source_dict.get("seeMoreUrl", ""))
                    if detail.get("contentType") == "IMAGE" and detail.get("messageType") == "GenerateContentQuery":
                        image_create_text = detail.get("text")
                return {
                    "text": message["text"],
                    "author": message["author"],
                    "source_keys": source_keys,
                    "source_values": source_values,
                    "suggestions": suggestions,
                    "image_create_text": image_create_text,
                    "messages_left": messages_left,
                    "max_messages": response["item"]["throttling"][
                        "maxNumUserMessagesInConversation"
                    ],
                }
        return {}

    async def ask_stream(
            self,
            prompt: str,
            wss_link: str = "wss://sydney.bing.com/sydney/ChatHub",
            conversation_style: CONVERSATION_STYLE_TYPE = None,
            raw: bool = False,
            webpage_context: str | None = None,
            search_result: bool = False,
            locale: str = guess_locale(),
            remove_options: list = None,
            add_options: list = None,
            attachment: dict | None = None
    ) -> Generator[bool, dict | str, None]:
        """
        Ask a question to the bot
        """
        async for response in self.chat_hub.ask_stream(
                prompt=prompt,
                conversation_style=conversation_style,
                wss_link=wss_link,
                raw=raw,
                webpage_context=webpage_context,
                search_result=search_result,
                locale=locale,
                remove_options=remove_options,
                add_options=add_options,
                attachment=attachment
        ):
            yield response

    async def close(self) -> None:
        """
        Close the connection
        """
        await self.chat_hub.close()

    async def reset(self) -> None:
        """
        Reset the conversation
        """
        await self.close()
        self.chat_hub = ChatHub(
            await Conversation.create(self.proxy, cookies=self.chat_hub.cookies, mode= "sydney"),
            proxy=self.proxy,
            cookies=self.chat_hub.cookies,
        )
