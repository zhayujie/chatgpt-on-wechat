from bot.session_manager import Session

"""
    e.g.  [{"id":23d977a3-2ffb-43a8-8c19-5f2f29c1fc7a,
                                "author":{"role":"system"},
                                "content":{"content_type":"text","parts":[""]}},
                               {"id":awdf5578-2ffb-43ae-8cg9-5f2qwe48fc7a,
                                "author":{"role":"user"},
                                "content":{"content_type":"text","parts":[create_message]},"metadata":{}}]
"""
class ChatgptHackSession(Session):
    def __init__(self, session_id, system_prompt=None, model="chatgpt_hack"):
        super().__init__(session_id, system_prompt)
        self.model = model
