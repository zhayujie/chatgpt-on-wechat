from bot.session_manager import Session
from common.log import logger

class SydneySession(Session):
    def __init__(self, session_id, system_prompt=None, model="sydney"):
        super().__init__(session_id, system_prompt)
        self.model = model
        self.reset()
     