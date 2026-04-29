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
        import plugins

        old_plugin_path = plugins.instance.current_plugin_path
        cow_cli_was_registered = "COW_CLI" in plugins.instance.plugins
        old_cow_cli_plugin = plugins.instance.plugins.get("COW_CLI")
        parent_had_cow_cli = hasattr(plugins, "cow_cli")
        old_parent_cow_cli = getattr(plugins, "cow_cli", None)
        module_names = ("plugins.cow_cli", "plugins.cow_cli.cow_cli")
        old_modules = {
            name: sys.modules[name]
            for name in module_names
            if name in sys.modules
        }
        plugins.instance.current_plugin_path = os.path.join(
            os.path.dirname(__file__), "..", "plugins", "cow_cli"
        )
        try:
            import plugins.cow_cli.cow_cli
            cow_cli_plugin = plugins.instance.plugins["COW_CLI"]
        finally:
            plugins.instance.current_plugin_path = old_plugin_path
            if cow_cli_was_registered:
                plugins.instance.plugins["COW_CLI"] = old_cow_cli_plugin
            else:
                plugins.instance.plugins.pop("COW_CLI", None)
            for name in module_names:
                if name in old_modules:
                    sys.modules[name] = old_modules[name]
                else:
                    sys.modules.pop(name, None)
            if parent_had_cow_cli:
                plugins.cow_cli = old_parent_cow_cli
            elif hasattr(plugins, "cow_cli"):
                delattr(plugins, "cow_cli")

        self.assertEqual(
            cow_cli_plugin._resolve_bot_type_for_model("ernie-4.5-turbo-128k"),
            const.QIANFAN,
        )
        self.assertEqual(
            cow_cli_plugin._resolve_bot_type_for_model("qianfan"),
            const.QIANFAN,
        )


if __name__ == "__main__":
    unittest.main()
