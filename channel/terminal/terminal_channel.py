from bridge.context import *
from channel.channel import Channel
import sys

class TerminalChannel(Channel):
    def startup(self):
        context = Context()
        print("\nPlease input your question")
        while True:
            try:
                prompt = self.get_input("User:\n")
            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit()

            context.type = ContextType.TEXT
            context['session_id'] = "User"
            context.content = prompt
            print("Bot:")
            sys.stdout.flush()
            res = super().build_reply_content(prompt, context).content
            print(res)


    def get_input(self, prompt):
        """
        Multi-line input function
        """
        print(prompt, end="")
        line = input()
        return line
