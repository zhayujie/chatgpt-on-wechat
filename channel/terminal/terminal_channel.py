from channel.channel import Channel
import sys

class TerminalChannel(Channel):
    def startup(self):
        context = {"from_user_id": "User"}
        print("\nPlease input your question")
        while True:
            try:
                prompt = self.get_input("User:\n")
            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit()

            print("Bot:")
            sys.stdout.flush()
            for res in super().build_reply_content(prompt, context):
                print(res, end="")
                sys.stdout.flush()
            print("\n")


    def get_input(self, prompt):
        """
        Multi-line input function
        """
        print(prompt, end="")
        line = input()
        return line
