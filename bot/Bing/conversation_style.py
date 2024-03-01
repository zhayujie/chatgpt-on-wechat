from enum import Enum

try:
    from typing import Literal, Union
except ImportError:
    from typing_extensions import Literal
from typing import Optional


class ConversationStyle(Enum):
    creative = [
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
        "deuct3"
    ]
    balanced = [
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
        "deuct3",
        # Balance
        "galileo",
        "gldcl1p"
    ]
    precise = [
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
        "deuct3",
        # Precise
        "h3precise"
    ]


CONVERSATION_STYLE_TYPE = Optional[
    Union[ConversationStyle, Literal["creative", "balanced", "precise"]]
]
