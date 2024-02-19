import base64
import json
import os
import pathlib
import random
import urllib.request
import uuid
from enum import Enum
from time import time
from typing import Union
import urllib.parse

import aiohttp
import binascii
import asyncio

_DEBUG = True

_PROXY = urllib.request.getproxies().get("https")

_BASE_OPTION_SETS = [
    # "fluxsydney",
	# "iyxapbing",
	# "iycapbing",
	# "clgalileoall",
	# "gencontentv3",
	# "nojbf"

    "fluxcopilot",
    "nojbf",
    "iyxapbing",
    "iycapbing",
    "dgencontentv3",
    "nointernalsugg",
    "disable_telemetry",
    "machine_affinity",
    "streamf",
    "codeint",
    "langdtwb",
    "fdwtlst",
    "fluxprod",
    "eredirecturl",
    # may related to image search
    "gptvnodesc",
    "gptvnoex",
]



class _OptionSets(Enum):
    CREATIVE = _BASE_OPTION_SETS + ["h3imaginative"]
    CREATIVECLASSIC = _BASE_OPTION_SETS + ["h3imaginative"]
    BALANCED = _BASE_OPTION_SETS + ["galileo"]
    PRECISE = _BASE_OPTION_SETS + ["h3precise"]
    DESIGNER = _BASE_OPTION_SETS + ["ai_persona_designer_gpt"] + ["h3imaginative"]
    #todo
    # case "Designer":
	# 	optionsSet = append(optionsSet, "ai_persona_designer_gpt")
	# 	options.ConversationStyle = "Creative"
	# 	gptId = "designer"


_SLICE_IDS = [
    "winmuid1tf",
    "newmma-prod",
    "imgchatgptv2",
    "tts2",
    "voicelang2",
    "anssupfotest",
    "emptyoson",
    "tempcacheread",
    "temptacache",
    "ctrlworkpay",
    "winlongmsg2tf",
    "628fabocs0",
    "531rai268s0",
    "602refusal",
    "621alllocs0",
    "621docxfmtho",
    "621preclsvn",
    "330uaug",
    "529rweas0",
    "0626snptrcs0",
    "619dagslnv1nr"
]


class _LocationHint(Enum):
    USA = {
        "locale": "en-US",
        "LocationHint": [
            {
                "country": "United States",
                "state": "California",
                "city": "Los Angeles",
                "timezoneoffset": 8,
                "countryConfidence": 8,
                "Center": {
                    "Latitude": 34.0536909,
                    "Longitude": -118.242766,
                },
                "RegionType": 2,
                "SourceType": 1,
            },
        ],
    }
    CHINA = {
        "locale": "zh-CN",
        "LocationHint": [
            {
                "country": "China",
                "state": "",
                "city": "Beijing",
                "timezoneoffset": 8,
                "countryConfidence": 8,
                "Center": {
                    "Latitude": 39.9042,
                    "Longitude": 116.4074,
                },
                "RegionType": 2,
                "SourceType": 1,
            },
        ],
    }
    EU = {
        "locale": "en-IE",
        "LocationHint": [
            {
                "country": "Norway",
                "state": "",
                "city": "Oslo",
                "timezoneoffset": 1,
                "countryConfidence": 8,
                "Center": {
                    "Latitude": 59.9139,
                    "Longitude": 10.7522,
                },
                "RegionType": 2,
                "SourceType": 1,
            },
        ],
    }
    UK = {
        "locale": "en-GB",
        "LocationHint": [
            {
                "country": "United Kingdom",
                "state": "",
                "city": "London",
                "timezoneoffset": 0,
                "countryConfidence": 8,
                "Center": {
                    "Latitude": 51.5074,
                    "Longitude": -0.1278,
                },
                "RegionType": 2,
                "SourceType": 1,
            },
        ],
    }

_DELIMITER = '\x1e'
_FORWARDED_IP = f"1.0.0.{random.randint(0, 255)}"

_ALLOWED_MESSAGE_TYPES = [
    "ActionRequest",
    "Chat",
    "Context",
    "InternalSearchQuery",
    "InternalSearchResult",
    "Disengaged",
    "InternalLoaderMessage",
    "Progress",
    "RenderCardRequest",
    "AdsQuery",
    "SemanticSerp",
    "GenerateContentQuery",
    "SearchQuery"
]
        
def sec_ms_gec():
    random_bytes = os.urandom(32)
    return binascii.hexlify(random_bytes).decode()

_HEADERS = {
    "accept": "application/json",
    "accept-language": "zh-CN,en;q=0.9",
    "content-type": "application/json",
    "sec-ch-ua": '"Microsoft Edge";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-full-version": '"113.0.1774.50"',
    "sec-ch-ua-full-version-list": '"Microsoft Edge";v="113.0.1774.50", "Chromium";v="113.0.5672.127", "Not-A.Brand";v="24.0.0.0"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": "",
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"15.0.0"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-ms-gec": sec_ms_gec(),
    "sec-ms-gec-version": "1-115.0.1866.1",
    "x-ms-client-request-id": str(uuid.uuid4()),
    "x-ms-useragent": "azsdk-js-api-client-factory/1.0.0-beta.1 core-rest-pipeline/1.10.0 OS/Win32",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.50",
    "Referer": "https://www.bing.com/search?q=Bing+AI&showconv=1",
    "Referrer-Policy": "origin-when-cross-origin",
    "x-forwarded-for": _FORWARDED_IP,
}

_HEADERS_INIT_CONVER = {
    "authority": "www.bing.com",
    "accept": "application/json",
    "accept-language": "zh-CN,en;q=0.9",
    "cache-control": "max-age=0",
    "sec-ch-ua": '"Chromium";v="110", "Not A(Brand";v="24", "Microsoft Edge";v="110"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-full-version": '"110.0.1587.69"',
    "sec-ch-ua-full-version-list": '"Chromium";v="110.0.5481.192", "Not A(Brand";v="24.0.0.0", "Microsoft Edge";v="110.0.1587.69"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"15.0.0"',
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.46",
    "x-edge-shopping-flag": "1",
    "x-forwarded-for": _FORWARDED_IP,
}

_HEADERS_INIT_CREATIMG = {
    "authority":                 "www.bing.com",
    "accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language":           "en-US,en;q=0.9",
    "cache-control":             "no-cache",
    "referer":                   "https://www.bing.com/search?q=Bing+AI&showconv=1",
    "upgrade-insecure-requests": "1",
    "user-agent":                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.46",
    "x-forwarded-for":           _FORWARDED_IP,
    "Sec-Fetch-Dest":            "iframe",
}



def _print(msg):
    if _DEBUG:
        print(msg)


def _format(msg: dict) -> str:
    return json.dumps(msg, ensure_ascii=False) + _DELIMITER


async def create_conversation(
        proxy: str | None = _PROXY,
        cookies: list[dict] | None = None,
):
    formatted_cookies = {}
    if cookies:
        for cookie in cookies:
            formatted_cookies[cookie["name"]] = cookie["value"]
    async with aiohttp.ClientSession(
            cookies=formatted_cookies,
            headers=_HEADERS_INIT_CONVER,
    ) as session:
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            response = await session.get(
                url="https://edgeservices.bing.com/edgesvc/turing/conversation/create",
                proxy=proxy,
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            print("Request timedout, retrying...")
            response = await session.get(
                url="https://edgeservices.bing.com/edgesvc/turing/conversation/create",
                proxy=proxy,
                timeout=timeout,
            )
    if response.status != 200:
        text = await response.text()
        raise Exception(f"Authentication failed {text}") 
    try:
        conversation = await response.json()
    except:
        text = await response.text()
        raise Exception(text)
    if conversation["result"]["value"] != "Success":
        raise Exception("failed to create the conversation: message: " + conversation["result"]["message"])
    if 'X-Sydney-Encryptedconversationsignature' in response.headers:
        conversation['sec_access_token'] = response.headers['X-Sydney-Encryptedconversationsignature']
    
    #todo Iterates over "set-cookie" headers, parses values, and logs modified cookies.
    # if 'set-cookie' in response.headers:
    #     modified_cookies = {}
    #     for cookie_header in response.headers['set-cookie']:
    #         # Split by semicolon and select first part before semicolon
    #         cookie_parts = cookie_header.split(';')[0].split('=')
    #         if len(cookie_parts) == 2:
    #             cookie_name, cookie_value = cookie_parts
    #             # Parse cookies from string (assuming appropriate function exists)
    #             parsed_cookie = parse_cookie(cookie_header)
    #             if parsed_cookie:
    #                 modified_cookies[cookie_name] = parsed_cookie

    #     # Log modified cookies for further action
    #     for cookie_name, cookie_value in modified_cookies.items():
    #         print(f"Modified cookie: {cookie_name} = {cookie_value}")

    #     # Update session cookies with modified values (if applicable)
    #     # ... (update logic based on framework/library)

    return conversation


def _get_location_hint_from_locale(locale: str) -> Union[dict, None]:
    locale = locale.lower()
    if locale == "en-gb":
        hint = _LocationHint.UK.value
    elif locale == "en-ie":
        hint = _LocationHint.EU.value
    elif locale == "zh-cn":
        hint = _LocationHint.CHINA.value
    else:
        hint = _LocationHint.USA.value
    return hint.get("LocationHint")


async def ask_stream(
        conversation: dict,
        prompt: str,
        context: str,
        conversation_style: str = "creative",
        locale: str = "zh-CN",
        proxy=_PROXY,
        image_url=None,
        wss_url='wss://sydney.bing.com/sydney/ChatHub',
        cookies: list[dict] | None = None,
        no_search: bool = False,
):
    timeout = aiohttp.ClientTimeout(total=900)
    formatted_cookies = {}
    if cookies:
        for cookie in cookies:
            formatted_cookies[cookie["name"]] = cookie["value"]
    async with aiohttp.ClientSession(timeout=timeout, cookies=formatted_cookies) as session:
        conversation_id = conversation["conversationId"]
        client_id = conversation["clientId"]
        sec_access_token = conversation["sec_access_token"] if 'sec_access_token' in conversation else None
        conversation_signature = conversation["conversationSignature"] if 'conversationSignature' in conversation else None
        message_id = str(uuid.uuid4())

        async with session.ws_connect(
                # wss_url,
                wss_url + ('?sec_access_token=' + urllib.parse.quote_plus(sec_access_token) if sec_access_token else ''),
                autoping=False,
                headers=_HEADERS,
                proxy=proxy
        ) as wss:
            await wss.send_str(_format({'protocol': 'json', 'version': 1}))
            await wss.receive(timeout=900)
            await wss.send_str(_format({"type": 6}))
            option_sets = getattr(_OptionSets, conversation_style.upper()).value.copy()
            if no_search:
                option_sets += 'nosearchall'

            struct = {
                'arguments': [
                    {
                        'optionsSets': option_sets,
                        'source': 'cib-ccp',
                        'allowedMessageTypes': _ALLOWED_MESSAGE_TYPES,
                        'sliceIds': _SLICE_IDS,
                        "verbosity": "verbose",
                        "scenario": "SERP",
                        'traceId': os.urandom(16).hex(),
                        'requestId': message_id,
                        'isStartOfSession': True,
                        'message': {
                            "locale": locale,
                            "market": locale,
                            "region": locale[-2:],  # en-US -> US
                            "locationHints": _get_location_hint_from_locale(locale),
                            "author": "user",
                            "inputMethod": "Keyboard",
                            "text": prompt,
                            "messageType": random.choice(["Chat", "CurrentWebpageContextRequest"]),
                            "requestId": message_id,
                            "messageId": message_id,
                            "imageUrl": image_url or None,
                        },
                        "tone": conversation_style.capitalize(),
                        'conversationSignature': conversation_signature if conversation_signature else None,
                        'participant': {
                            'id': client_id
                        },
                        "spokenTextMode": "None",
                        'conversationId': conversation_id,
                        'previousMessages': [
                            {
                                "author": "user",
                                "description": context,
                                "contextType": "WebPage",
                                "messageType": "Context",
                                # "messageId": "discover-web--page-ping-mriduna-----",
                            },
                        ],
                        'gptId': "copilot",
                    }
                ],
                'invocationId': '0',
                'target': 'chat',
                'type': 4
            }

            # struct = json.loads(pathlib.Path('struct.json').read_text())
            # struct['arguments'][0]['optionsSets'] = option_sets
            # struct['arguments'][0]['sliceIds'] = _SLICE_IDS
            # struct['arguments'][0]['traceId'] = struct1['arguments'][0]['traceId']
            # struct['arguments'][0]['requestId'] = message_id
            # struct['arguments'][0]['message']['requestId'] = message_id
            # struct['arguments'][0]['message']['messageId'] = message_id
            # struct['arguments'][0]['conversationSignature'] = conversation_signature
            # struct['arguments'][0]['conversationId'] = conversation_id
            # struct['arguments'][0]['previousMessages'] = struct1['arguments'][0]['previousMessages']

            await wss.send_str(_format(struct))
            _print(f'Sent:\n{json.dumps(struct)}')

            retry_count = 5
            while True:
                if wss.closed:
                    break
                msg = await wss.receive(timeout=900)

                if not msg.data:
                    retry_count -= 1
                    if retry_count == 0:
                        raise Exception("No response from server")
                    continue

                if isinstance(msg.data, str):
                    objects = msg.data.split(_DELIMITER)
                else:
                    continue

                for obj in objects:
                    if int(time()) % 6 == 0:
                        await wss.send_str(_format({"type": 6}))
                        _print(f'Sent:\n{json.dumps({"type": 6})}')
                    if not obj:
                        continue
                    response = json.loads(obj)
                    _print(f'Received:\n{obj}')
                    if response["type"] == 2:
                        if response["item"]["result"].get("error"):
                            raise Exception(
                                f"{response['item']['result']['value']}: {response['item']['result']['message']}")
                    yield response
                    if response["type"] == 2:
                        break


async def upload_image(filename=None, img_base64=None, proxy=None):
    async with aiohttp.ClientSession(
            headers={"Referer": "https://www.bing.com/search?q=Bing+AI&showconv=1&FORM=hpcodx"}
    ) as session:
        timeout = aiohttp.ClientTimeout(total=90)
        url = "https://www.bing.com/images/kblob"

        payload = {
            "imageInfo": {},
            "knowledgeRequest": {
                "invokedSkills": ["ImageById"],
                "subscriptionId": "Bing.Chat.Multimodal",
                "invokedSkillsRequestData": {"enableFaceBlur": False},
                "convoData": {
                    "convoid": "",
                    "convotone": "Creative"
                }
            }
        }

        if filename is not None:
            with open(filename, 'rb') as f:
                file_data = f.read()
                image_base64 = base64.b64encode(file_data)
        elif img_base64 is not None:
            image_base64 = img_base64
        else:
            raise Exception('no image provided')

        data = aiohttp.FormData()
        data.add_field('knowledgeRequest', json.dumps(payload), content_type="application/json")
        data.add_field('imageBase64', image_base64.decode('utf-8'), content_type="application/octet-stream")
        try:
            async with session.post(url, data=data, proxy=proxy, timeout= timeout) as resp:
                return (await resp.json())["blobId"]
        except asyncio.TimeoutError:
            raise Exception("Timedout please try again!")

#todo image create
# @dataclass
# class GenerativeImage:
#     text: str
#     url: str

# @dataclass
# class GenerateImageResult:
#     generative_image: GenerativeImage
#     image_urls: list[str]
#     # duration: float  # Representing time.Duration in Python
# import re
# import asyncio
# async def generate_image(
#     proxy: str | None = _PROXY,
#     generative_image: GenerativeImage | None = None,
#     cookies: list[dict] | None = None,
# ) -> (GenerateImageResult, Exception | None):

#     formatted_cookies = {}
#     if cookies:
#         for cookie in cookies:
#             formatted_cookies[cookie["name"]] = cookie["value"]

#     async with aiohttp.ClientSession(
#         headers=_HEADERS_INIT_CREATIMG, cookies=formatted_cookies
#     ) as session:
#         try:
#             async with session.get(generative_image.url, proxy=proxy) as resp:
#                 resp.raise_for_status()
#                 text = await resp.text()

#                 # Extract result ID
#                 matches = re.findall(
#                     r"/images/create/async/results/(.*?)\?", text
#                 )
#                 if not matches or len(matches) < 2:
#                     return None, Exception("Cannot find image creation result")
#                 result_id = matches[1]

#                 # Await image creation
#                 result_url = f"https://www.bing.com/images/create/async/results/{result_id}?q={urllib.parse.quote(generative_image.text)}&partner=sydney&showselective=1&IID=images.as"
#                 for _ in range(15):
#                     await asyncio.sleep(3)
#                     async with session.get(result_url, proxy=proxy) as result_resp:
#                         result_resp.raise_for_status()
#                         text = await result_resp.text()

#                         # Check for rejection
#                         if "Please try again or come back later" in text:
#                             return None, Exception("Prompt rejected by Bing")

#                         # Extract image URLs
#                         image_urls = re.findall(r'<img class="mimg".*?src="(.*?)"', text)
#                         if image_urls:
#                             return GenerateImageResult(
#                                 generate_image=generative_image,
#                                 image_urls=image_urls,
#                             ), None

#         except aiohttp.ClientError as err:
#             return None, err

#     return None, Exception("Image creation timeout")