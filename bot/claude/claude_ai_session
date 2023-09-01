from bot.session_manager import Session


class ClaudeAiSession(Session):
    def __init__(self, session_id, system_prompt=None, model="claude"):
        super().__init__(session_id, system_prompt)
        self.model = model
        # claude逆向不支持role prompt
        # self.reset()
