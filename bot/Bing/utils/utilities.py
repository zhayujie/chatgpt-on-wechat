import json
import locale
import random
import sys
from typing import Union

from ..constants import DELIMITER
from ..locale import LocationHint


def append_identifier(msg: dict) -> str:
    # Convert dict to json string
    return json.dumps(msg, ensure_ascii=False) + DELIMITER


def get_ran_hex(length: int = 32) -> str:
    return "".join(random.choice("0123456789abcdef") for _ in range(length))


def get_location_hint_from_locale(locale_str: str) -> Union[dict, None]:
    locale_str = locale_str.lower()
    if locale_str == "en-gb":
        hint = LocationHint.UK.value
    elif locale_str == "en-ie":
        hint = LocationHint.EU.value
    elif locale_str == "zh-cn":
        hint = LocationHint.CHINA.value
    else:
        hint = LocationHint.USA.value
    return hint.get("LocationHint")


def guess_locale() -> str:
    if sys.platform.startswith("win"):
        return "en-us"
    loc, _ = locale.getlocale()
    return loc.replace("_", "-") if loc else "en-us"
