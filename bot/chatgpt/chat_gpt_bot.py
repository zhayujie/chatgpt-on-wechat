import time
from bot.bot import Bot
from revChatGPT.revChatGPT import Chatbot

config = {
    "Authorization": "<Your Bearer Token Here>",  # This is optional
    "session_token": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..n8p94letJscz9y64.vgWOg1sSU7Wkoxbs81kTB_9rGgXQVmc6i9LgBHzo-EsUatVV-PsGKiAc9g8gaTaAf1pM_QW53ECH7b2Ge80ie2Q-EAsx-qdiLdwfggwob3dXk3zTQmK5pL8_aVNQ1YoMzQNciBXUbHdZhwzZrXPEsXr5eocjNm2fD5LcTR4cBwH4LRo9Z4AZsFBg9SJ9miQLLBdtkBmjWNQfwM_OHhlAKOYAT_aR1e3E0M6M173xbyvsBLwzQ5ol6Fu5ui7to6SSYejen518pm9vDkV3QRaJ6u0W9t8OEbnaTOCv-JR_7_UNgD5dBlRnj4nyh38vj9yGpW9fm6D7HDmUtF5X2RlmECdQBxsJI-Xk0fETqgjsPGC7O2kNJduW2ukwzMN9KaEVlONQYwfZ73TA6-5jXkvkD3rq3qnsWFGoju5GP11RpbgXKxeHBOZzslja6xPQVPSbkwEVsON_JTyOKcCrzP-vlPXWm51ZyE5hYsjhf3h1UonlpxQRuqM9EnKiajetV8gdbBF5QkhdSoGYQhwPZ1sdUQ197GmpWdgMQgnh9VBcpVP-GWB_yAM4Yj4AAJ79Jh4hkUy2YrGaSu3X3jqBZBfy3SXymcGZZpEHU8-jTovw4wFctVpK3l1fAGHppGpbS0mTciXh0-Vw5F1unIYe6v-y-vEPGmhx8wjukruSlagW1vvklHVsj8zIg0cUEU112w18MuxqzpFMa1LBr8Lr6hbODJX_I67QV1LvyVdFGygxtKzOj9sm-ZZFibv2vrXoIGWRutxlmxz1BiCWldFUjNw9S4oSEDe_mk3WommuY7MCt15Ufa4JOmerZD-P2aK-cylfwFgQJhl8Xx2bwSh8feY404p_pgIcaN8Oex5qSkXiz_MChNPbLSysDB7eXPaUDRWP1kVVaye6MLAmOT8RtAsIWjO3Ky6z5j4nE2FtUMNFMiG79iLFj6NSZ4l-8xdpYgvdsEh9pUfAO5zY_WqOwxb1v4ckKIII_3ZZQTz8t3KePJc4jqpvvmFa30agldub9nYglcDS95zDLrboqYF2opNNuVlDrZsXzJHH-t43S5H34dnUY8jENn_qe83DcgV6FJaUI-iln5h_Z0xvRNXi-HFXwavwC2i0otHsUO60fvRThrmv6pgzYVXqbEY4JO_pWbiH_qdxJ4Ky1LKGRHcfw9Kmn32qZhQptbSNPyP3irrC8_DKATbi2q-0gQ314Loc2VJGphvW9qmsBC8MXjdyZMYqZcXHcoed-E5_JgDWPaSfdrrpfP_ct1uis-x-yIdylLK8wQ7XHuCxfHVUDePqbLw59XUYOO7TVRi5tPvoh8-J0fvYHwGqLUSULAEV0AfggYOIMODHgq_tCLHOZMVEKzvGspPtvBtZUU64F-l4XWX9AwRqmWD654lhV3BR1Ea7FEVh1Mb1trntcd6JGMERqHVFoLxlbTk7_BFWGwfjPSs-8uzR7MBYVXMmscmICzHp_EJbG1zqmrZfszN_TS5pXB5sKKoe8bEJpDznCa3GlyQxlftMYFtyTXGmi8N7M-ZxPBHX0SIlsuunaKoNAKTqJM5rezn1iXZYANkDgom115sc6rpILNgTUQMzJawYmnVNjtfdLEHRBpPymPohlMwCPTst3Fh0xNaUUg7lEAIfFWRnl-lAxxqpTb1z1nz_6fqaNXEa4be9cxr23LLnz7XESan4nQSvusewWKdOO3HP4MoubrCE1rfVY68vG6mg3eV78dMy40_8ee40p0eYVdRSCBXJg-QSFCd8no0BCCFI0QhQ_rc3Al6boIaGun6UhsTSsHudSAUHuwRS1FpsxHo7X2jI80avFUuNtZhRCgNSru81hfozNhf7X5K46Fq5MQpRY32CMxTYu6hSfSdlvtbnVvaFiLLxqAg73Gr7L7Je2BAy1Feg6b13JMkEWObDnA1GhdWVs6p81MSB4Id2vFKpUaIjuJDuW2PTnE0BQCHtUhxbgac9yqyx3L7IlURrCvaAs31LtU9KsPJhE-_vjss3rKMY51xBKMxThwP7UP90mXm9llUnFzdho9jERYEPigJMSyZBSHTiETU-fHg3JcQbGs3ncrTdd_EDieEEgugYcxkJtt4QuUuiRoK3jTf8T0UbqEZWihtp_quSuyWXHSdtY2XbzHrY3cWeUhdmTsg6VdWQVM7R2BlXj0tbRN3mhpggLXVIeJskp8h7MLOo90DlwX8j2sSWTggVjVLmL39dk2MV0orevquoLmZNg2vP_dYs-w7nJLRI1jdvYw3T87JlEV09gRL_YCzdr5vBx1PcAEkSe6E5W0qI6rXXNZ7DpXoCHAlVVuxgtW_nz7zkCv1twhYYTRCpI6TdIVCOcMU_D06-WYNgflzzqz_Cm2J5lHu4.UeCj_srwxF4V4x92z7lAjA"
}
chatbot = Chatbot(config)
user_session = dict()
last_session_refresh = time.time()


class ChatGPTBot(Bot):
    def reply(self, query, context=None):

        from_user_id = context['from_user_id']
        print("[GPT]query={}, user_id={}, session={}".format(query, from_user_id, user_session))

        now = time.time()
        global last_session_refresh
        if now - last_session_refresh > 60 * 8:
            print('[GPT]session refresh, now={}, last={}'.format(now, last_session_refresh))
            chatbot.refresh_session()
        last_session_refresh = now

        if from_user_id in user_session:
            if time.time() - user_session[from_user_id]['last_reply_time'] < 60 * 5:
                chatbot.conversation_id = user_session[from_user_id]['conversation_id']
                chatbot.parent_id = user_session[from_user_id]['parent_id']
            else:
                chatbot.reset_chat()
        else:
            chatbot.reset_chat()

        print("[GPT]convId={}, parentId={}".format(chatbot.conversation_id, chatbot.parent_id))



        try:
            res = chatbot.get_chat_response(query, output="text")
            print("[GPT]userId={}, res={}".format(from_user_id, res))

            user_cache = dict()
            user_cache['last_reply_time'] = time.time()
            user_cache['conversation_id'] = res['conversation_id']
            user_cache['parent_id'] = res['parent_id']
            user_session[from_user_id] = user_cache
            return res['message']
        except Exception as e:
            print(e)
            return None
