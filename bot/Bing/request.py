import uuid
from datetime import datetime
from typing import Union

from .conversation_style import CONVERSATION_STYLE_TYPE
from .conversation_style import ConversationStyle
from .utils.utilities import get_location_hint_from_locale
from .utils.utilities import get_ran_hex
from .utils.utilities import guess_locale


class ChatHubRequest:
    def __init__(
            self,
            conversation_signature: str,
            client_id: str,
            conversation_id: str,
            invocation_id: int = 3,
    ) -> None:
        self.struct: dict = {}

        self.client_id: str = client_id
        self.conversation_id: str = conversation_id
        self.conversation_signature: str = conversation_signature
        self.invocation_id: int = invocation_id

    def update(
            self,
            prompt: str,
            conversation_style: CONVERSATION_STYLE_TYPE,
            webpage_context: Union[str, None] = None,
            search_result: bool = False,
            locale: str = guess_locale(),
            image_url: str = None
    ) -> None:
        if conversation_style:
            if not isinstance(conversation_style, ConversationStyle):
                conversation_style = getattr(ConversationStyle, conversation_style)
        message_id = str(uuid.uuid4())
        # Get the current local time
        now_local = datetime.now()

        # Get the current UTC time
        now_utc = datetime.utcnow()

        # Calculate the time difference between local and UTC time
        timezone_offset = now_local - now_utc

        # Get the offset in hours and minutes
        offset_hours = int(timezone_offset.total_seconds() // 3600)
        offset_minutes = int((timezone_offset.total_seconds() % 3600) // 60)

        # Format the offset as a string
        offset_string = f"{offset_hours:+03d}:{offset_minutes:02d}"

        # Get current time
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + offset_string
        self.struct = {
            "arguments": [
                {
                    "source": "cib",
                    "optionsSets": conversation_style.value,
                    "allowedMessageTypes": [
                        "ActionRequest",
                        "Chat",
                        "Context",
                        "InternalSearchQuery",
                        "InternalSearchResult",
                        "InternalLoaderMessage",
                        "Progress",
                        "GenerateContentQuery",
                        "SearchQuery",
                        "GeneratedCode",
                    ],
                    "sliceIds": [
                        "schurmsg",
                        "ntbkcf",
                        "rankcf",
                        "bgstreamcf",
                        "cmcallapptf",
                        "vnextvoicecf",
                        "tts5cf",
                        "abv2mobcf",
                        "ctvismctrl",
                        "suppsm240rev10-t",
                        "suppsm240-t",
                        "translrefctrl",
                        "1215perscs0",
                        "0212bops0",
                        "116langwb",
                        "0112wtlsts0",
                        "118wcsmw",
                        "1201reasons0",
                        "0116trimgd",
                        "cacfastapis"
                    ],
                    "verbosity": "verbose",
                    "scenario":"SERP",
                    "traceId": get_ran_hex(32),
                    "isStartOfSession": self.invocation_id == 3,
                    "message": {
                        "locale": locale,
                        "market": locale,
                        "region": locale[-2:],  # en-US -> US
                        "locationHints": get_location_hint_from_locale(locale),
                        "timestamp": timestamp,
                        "author": "user",
                        "inputMethod": "Keyboard",
                        "text": prompt,
                        "messageType": "Chat",
                        "messageId": message_id,
                        "requestId": message_id,
                        "imageUrl": image_url if image_url else None,
                        "originalImageUrl": image_url if image_url else None,
                    },
                    "tone": conversation_style.name.capitalize(),  # Make first letter uppercase
                    "requestId": message_id,
                    "conversationSignature": self.conversation_signature,
                    "participant": {
                        "id": self.client_id,
                    },
                    "conversationId": self.conversation_id,
                },
            ],
            "invocationId": str(self.invocation_id),
            "target": "chat",
            "type": 4,
        }
        if search_result:
            have_search_result = [
                "InternalSearchQuery",
                "InternalSearchResult",
                "InternalLoaderMessage",
                "RenderCardRequest",
            ]
            self.struct["arguments"][0]["allowedMessageTypes"] += have_search_result
        if webpage_context:
            self.struct["arguments"][0]["previousMessages"] = [
                {
                    "author": "user",
                    "description": webpage_context,
                    "contextType": "WebPage",
                    "messageType": "Context",
                    "messageId": "discover-web--page-ping-mriduna-----",
                },
            ]
        self.invocation_id += 1

        # print(timestamp)
