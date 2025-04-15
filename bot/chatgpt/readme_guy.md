1.仅修改在chat_gpt_bot.py中,引入clent.py定义的MCPClient类,用于加入mcp服务作为中介，
    在chat_gpt_bot.py自定义了gy_getanswer(self,querystr)

2.本目录下的client.py 用于方便测试，是上两级guymcp目录下的client.py的副本，两者完全一致 
    对应导入为from bot.chatgpt.client import MCPClient
    
3.test_client.py 用于测试client.py

