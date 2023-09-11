class _imgCache:
    def __init__(self, sessionid, instruct, prompt):
        self.cache = {}
        self.sessionid = sessionid
        self.instruct = instruct
        self.prompt = prompt
        self.base64Array = []

    def reset(self):
        self.instruct = ""
        self.prompt = ""
        self.base64Array = []

    def get_cache(self):
        return {
            "instruct": self.instruct if self.instruct else "",
            "prompt": self.prompt if self.prompt else "",
            "base64": self.base64Array[len(self.base64Array) - 1] if self.base64Array else "",
            "base64Array": self.base64Array if self.base64Array else []
        }

    def action(self, base64):
        self.base64Array.append(base64)
        return {
            "instruct": self.instruct,
            "prompt": self.prompt,
            "base64": base64,
            "base64Array": self.base64Array
        }
