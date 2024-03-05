import json
import os
from typing import List
from typing import Union

import httpx

from .constants import HEADERS_INIT_CONVER, BUNDLE_VERSION, SYDNEY_INIT_HEADER
from .proxy import get_proxy
from .utils.exception.exceptions import NotAllowedToAccess, AuthCookieError


class Conversation:
    def __init__(
            self,
            proxy: Union[str, None] = None,
            async_mode: bool = False,
            cookies: Union[List[dict], None] = None,
            mode: str = "Bing"
    ) -> None:
        if async_mode:
            return
        self.struct: dict = {
            "conversationId": None,
            "clientId": None,
            "conversationSignature": None,
            "result": {"value": "Success", "message": None},
        }
        self.proxy = proxy
        proxy = (
                proxy
                or os.environ.get("all_proxy")
                or os.environ.get("ALL_PROXY")
                or os.environ.get("https_proxy")
                or os.environ.get("HTTPS_PROXY")
                or None
        )
        if proxy is not None and proxy.startswith("socks5h://"):
            proxy = "socks5://" + proxy[len("socks5h://"):]
        if mode == "Bing":
            header = HEADERS_INIT_CONVER
        else:
            header = SYDNEY_INIT_HEADER
        self.session = httpx.Client(
            proxies=proxy,
            timeout=900,
            headers=header,
        )
        if cookies:
            for cookie in cookies:
                self.session.cookies.set(cookie["name"], cookie["value"])
        # Send GET request
        if mode == "Bing":
            response = self.session.get(
                url=os.environ.get("BING_PROXY_URL")
                    or f"https://www.bing.com/turing/conversation/create"
                       f"?bundleVersion={BUNDLE_VERSION}",
            )
        else:
            response = self.session.get(
                url=os.environ.get("BING_PROXY_URL")
                    or f"https://edgeservices.bing.com/edgesvc/turing/conversation/create"
                       f"?bundleVersion={BUNDLE_VERSION}",
            )
        if response.status_code != 200:
            print(f"Status code: {response.status_code}")
            print(response.text)
            print(response.url)
            raise AuthCookieError("Authentication failed")
        try:
            self.struct = response.json()
            if self.struct.get("conversationSignature") is None:
                self.struct["conversationSignature"] = response.headers["X-Sydney-Conversationsignature"]
                self.struct["encryptedConversationSignature"] = response.headers[
                    "X-Sydney-Encryptedconversationsignature"]
        except (json.decoder.JSONDecodeError, NotAllowedToAccess) as exc:
            raise AuthCookieError(
                "Authentication failed. You have not been accepted into the beta.",
            ) from exc
        if self.struct["result"]["value"] == "UnauthorizedRequest":
            raise NotAllowedToAccess(self.struct["result"]["message"])

    @staticmethod
    async def create(
            proxy: Union[str, None] = None,
            cookies: Union[List[dict], None] = None,
            mode: str | None = None
    ) -> "Conversation":
        self = Conversation(async_mode=True)
        self.struct = {
            "conversationId": None,
            "clientId": None,
            "conversationSignature": None,
            "result": {"value": "Success", "message": None},
        }
        self.proxy = get_proxy(proxy)
        transport = httpx.AsyncHTTPTransport(retries=900)
        # Convert cookie format to httpx format
        formatted_cookies = None
        if cookies:
            formatted_cookies = httpx.Cookies()
            for cookie in cookies:
                formatted_cookies.set(cookie["name"], cookie["value"])
        async with httpx.AsyncClient(
                proxies=proxy,
                timeout=30,
                headers=HEADERS_INIT_CONVER,
                transport=transport,
                cookies=formatted_cookies,
        ) as client:
            # Send GET request
            if mode == "Bing":
                response = await client.get(
                    url=os.environ.get("BING_PROXY_URL")
                        or f"https://www.bing.com/turing/conversation/create"
                           f"?bundleVersion={BUNDLE_VERSION}",
                    follow_redirects=True,
                )
            else:
                response = await client.get(
                    url=os.environ.get("BING_PROXY_URL")
                        or f"https://copilot.microsoft.com/turing/conversation/create"
                           f"?bundleVersion={BUNDLE_VERSION}",
                    follow_redirects=True,
                )
        if response.status_code != 200:
            print(f"Status code: {response.status_code}")
            print(response.text)
            print(response.url)
            raise AuthCookieError("Authentication failed")
        try:
            self.struct = response.json()
            if self.struct.get("conversationSignature") is None:
                self.struct["conversationSignature"] = response.headers["X-Sydney-Conversationsignature"]
                self.struct["encryptedConversationSignature"] = response.headers[
                    "X-Sydney-Encryptedconversationsignature"]
        except (json.decoder.JSONDecodeError, NotAllowedToAccess) as exc:
            print(response.text)
            raise AuthCookieError(
                "Authentication failed. You have not been accepted into the beta.",
            ) from exc
        if self.struct["result"]["value"] == "UnauthorizedRequest":
            raise NotAllowedToAccess(self.struct["result"]["message"])
        return self
