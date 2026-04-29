# encoding:utf-8
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestQianfanConstantsAndRouting(unittest.TestCase):
    def test_qianfan_provider_constant_defined(self):
        from common import const

        self.assertEqual(const.QIANFAN, "qianfan")

    def test_ernie_constants_are_in_model_list(self):
        from common import const

        self.assertEqual(const.ERNIE_45_TURBO_128K, "ernie-4.5-turbo-128k")
        self.assertEqual(const.ERNIE_45_TURBO_32K, "ernie-4.5-turbo-32k")
        self.assertEqual(const.ERNIE_X1_TURBO_32K, "ernie-x1-turbo-32k")
        self.assertIn(const.QIANFAN, const.MODEL_LIST)
        self.assertIn(const.ERNIE_45_TURBO_128K, const.MODEL_LIST)
        self.assertIn(const.ERNIE_45_TURBO_32K, const.MODEL_LIST)
        self.assertIn(const.ERNIE_X1_TURBO_32K, const.MODEL_LIST)

    def test_qianfan_config_keys_are_available(self):
        import config

        self.assertIn("qianfan_api_key", config.available_setting)
        self.assertIn("qianfan_api_base", config.available_setting)

    def test_agent_bridge_routes_ernie_models_to_qianfan(self):
        from bridge.agent_bridge import AgentLLMModel
        from common import const

        model = AgentLLMModel.__new__(AgentLLMModel)
        fake_conf = MagicMock()
        fake_conf.get.side_effect = lambda key, default=None: {
            "use_linkai": False,
            "linkai_api_key": "",
            "bot_type": "",
        }.get(key, default)

        with patch("bridge.agent_bridge.conf", return_value=fake_conf):
            self.assertEqual(
                AgentLLMModel._resolve_bot_type(model, "ernie-4.5-turbo-128k"),
                const.QIANFAN,
            )
            self.assertEqual(
                AgentLLMModel._resolve_bot_type(model, "qianfan"),
                const.QIANFAN,
            )

    def test_cow_cli_routes_ernie_models_to_qianfan(self):
        from common import const
        from plugins.cow_cli.cow_cli import CowCli

        self.assertEqual(
            CowCli._resolve_bot_type_for_model("ernie-4.5-turbo-128k"),
            const.QIANFAN,
        )
        self.assertEqual(
            CowCli._resolve_bot_type_for_model("qianfan"),
            const.QIANFAN,
        )


if __name__ == "__main__":
    unittest.main()
