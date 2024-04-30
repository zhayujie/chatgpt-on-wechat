from omnivoreql import OmnivoreQL
from dotenv import load_dotenv
import os

load_dotenv()

OMNIVORE_API_KEY = os.getenv("OMNIVORE_API_KEY")

if OMNIVORE_API_KEY is None:
    raise ValueError("OMNIVORE_API_KEY not found in environment variables")


def save_url2omni(url):
    omnivoreql_client = OmnivoreQL(OMNIVORE_API_KEY)
    result = omnivoreql_client.save_url(url)
    return result

