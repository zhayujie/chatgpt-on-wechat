from bot.session_manager import Session
from common.log import logger
class OpenAISession(Session):
    def __init__(self, session_id, system_prompt=None, model= "text-davinci-003"):
        super().__init__(session_id, system_prompt)
        self.conversation = []
        self.model = model
        self.reset()
    
    def reset(self):
        pass

    def add_query(self, query):
        question = {'type': 'question', 'content': query}
        self.conversation.append(question)

    def add_reply(self, reply):
        answer = {'type': 'answer', 'content': reply}
        self.conversation.append(answer)
    def __str__(self):
        '''
        e.g.  Q: xxx
              A: xxx
              Q: xxx
        '''
        prompt = self.system_prompt
        if prompt:
            prompt += "<|endoftext|>\n\n\n"
        for item in self.conversation:
            if item['type'] == 'question':
                prompt += "Q: " + item['content'] + "\n"
            elif item['type'] == 'answer':
                prompt += "\n\nA: " + item['content'] + "<|endoftext|>\n"

        if len(self.conversation) > 0 and self.conversation[-1]['type'] == 'question':
            prompt += "A: "
        return prompt

    def discard_exceeding(self, max_tokens, cur_tokens= None):
        precise = True
        try:
            cur_tokens = num_tokens_from_string(str(self), self.model)
        except Exception as e:
            precise = False
            if cur_tokens is None:
                raise e
            logger.debug("Exception when counting tokens precisely for query: {}".format(e))
        while cur_tokens > max_tokens:
            if len(self.conversation) > 1:
                self.conversation.pop(0)
            elif len(self.conversation) == 1 and self.conversation[0]["type"] == "answer":
                self.conversation.pop(0)
                if precise:
                    cur_tokens = num_tokens_from_string(str(self), self.model)
                else:
                    cur_tokens = len(str(self))
                break
            elif len(self.conversation) == 1 and self.conversation[0]["type"] == "question":
                logger.warn("user question exceed max_tokens. total_tokens={}".format(cur_tokens))
                break
            else:
                logger.debug("max_tokens={}, total_tokens={}, len(conversation)={}".format(max_tokens, cur_tokens, len(self.conversation)))
                break
            if precise:
                cur_tokens = num_tokens_from_string(str(self), self.model)
            else:
                cur_tokens = len(str(self))
        return cur_tokens
    

# refer to https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
def num_tokens_from_string(string: str, model: str) -> int:
    """Returns the number of tokens in a text string."""
    import tiktoken
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string,disallowed_special=()))
    return num_tokens