"""
CowCli plugin - Intercept cow/slash commands in chat messages.

Matches messages like:
  cow skill list
  cow context clear
  /skill list
  /context clear
  /status

Does NOT match:
  cow是什么
  cow真好用
  /开头但不是已知命令
"""

import os
import threading

import plugins
from plugins import Plugin, Event, EventContext, EventAction
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from cli import __version__


# Known top-level subcommands that cow supports
KNOWN_COMMANDS = {
    "help", "version", "status", "logs",
    "start", "stop", "restart",
    "skill", "context", "config",
}

# Commands that can only run from the CLI (terminal), not in chat
CLI_ONLY_COMMANDS = {"start", "stop", "restart"}

# Commands that can only run from chat (need access to in-process memory)
CHAT_ONLY_COMMANDS = set()  # context is allowed in both, but behaves differently


@plugins.register(
    name="cow_cli",
    desc="Handle cow/slash commands in chat messages",
    version="0.1.0",
    author="CowAgent",
    desire_priority=1000,
)
class CowCliPlugin(Plugin):

    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.debug("[CowCli] initialized")

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type != ContextType.TEXT:
            return

        content = e_context["context"].content.strip()
        parsed = self._parse_command(content)
        if not parsed:
            return

        cmd, args = parsed
        logger.info(f"[CowCli] intercepted command: {cmd} {args}")

        result = self._dispatch(cmd, args, e_context)

        reply = Reply(ReplyType.TEXT, result)
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS

    def _parse_command(self, content: str):
        """
        Parse cow command from message text.

        Supported formats:
          cow <command> [args...]   e.g. "cow skill list"
          /<command> [args...]      e.g. "/skill list"

        Returns (command, args_string) or None if not a cow command.
        """
        parts = None

        if content.startswith("/"):
            rest = content[1:].strip()
            if rest:
                parts = rest.split(None, 1)
        elif content.startswith("cow "):
            rest = content[4:].strip()
            if rest:
                parts = rest.split(None, 1)

        if not parts:
            return None

        cmd = parts[0].lower()
        if cmd not in KNOWN_COMMANDS:
            return None

        args = parts[1] if len(parts) > 1 else ""
        return cmd, args

    # ------------------------------------------------------------------
    # Command dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, cmd: str, args: str, e_context: EventContext) -> str:
        if cmd in CLI_ONLY_COMMANDS:
            return f"⚠️ `cow {cmd}` 只能在命令行终端中执行。\n请在终端运行: cow {cmd}"

        handler = getattr(self, f"_cmd_{cmd}", None)
        if handler:
            try:
                return handler(args, e_context)
            except Exception as e:
                logger.error(f"[CowCli] command '{cmd}' failed: {e}")
                return f"命令执行失败: {e}"

        return f"未知命令: {cmd}"

    # ------------------------------------------------------------------
    # help / version
    # ------------------------------------------------------------------

    def _cmd_help(self, args: str, e_context: EventContext) -> str:
        lines = [
            "📋 CowAgent 命令列表",
            "",
            "  /help          显示此帮助",
            "  /version       查看版本",
            "  /status        查看运行状态",
            "  /logs [N]      查看最近N条日志 (默认20)",
            "  /context       查看当前对话上下文信息",
            "  /context clear 清除当前对话上下文",
            "  /skill list    查看已安装的技能",
            "  /skill list --remote  浏览技能广场",
            "  /skill search <关键词>  搜索技能",
            "  /skill install <名称>  安装技能",
            "  /skill info <名称>  查看技能详情",
            "  /config              查看当前配置",
            "  /config <key>        查看某项配置",
            "  /config <key> <val>  修改配置",
            "",
            "💡 也可以用 cow <command> 代替 /<command>",
        ]
        return "\n".join(lines)

    def _cmd_version(self, args: str, e_context: EventContext) -> str:
        return f"CowAgent v{__version__}"

    # ------------------------------------------------------------------
    # status
    # ------------------------------------------------------------------

    def _cmd_status(self, args: str, e_context: EventContext) -> str:
        from config import conf

        cfg = conf()
        lines = ["📊 CowAgent 运行状态", ""]

        lines.append(f"  版本: v{__version__}")
        lines.append(f"  进程: PID {os.getpid()}")

        channel = cfg.get("channel_type", "unknown")
        if isinstance(channel, list):
            channel = ", ".join(channel)
        lines.append(f"  通道: {channel}")

        model_name = cfg.get("model", "unknown")
        lines.append(f"  模型: {model_name}")

        mode = "Agent" if cfg.get("agent") else "Chat"
        lines.append(f"  模式: {mode}")

        session_id = self._get_session_id(e_context)
        agent = self._get_agent(session_id)
        if agent:
            lines.append("")
            with agent.messages_lock:
                msg_count = len(agent.messages)
            lines.append(f"  会话消息数: {msg_count}")

            if agent.skill_manager:
                total = len(agent.skill_manager.skills)
                enabled = sum(
                    1 for v in agent.skill_manager.skills_config.values()
                    if v.get("enabled", True)
                )
                lines.append(f"  已加载技能: {enabled}/{total}")
        else:
            lines.append("")
            lines.append(f"  Agent: 未初始化 (首次对话后自动创建)")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # logs
    # ------------------------------------------------------------------

    def _cmd_logs(self, args: str, e_context: EventContext) -> str:
        num_lines = 20
        if args.strip().isdigit():
            num_lines = min(int(args.strip()), 50)

        log_file = self._find_log_file()
        if not log_file:
            return "未找到日志文件"

        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
            tail = all_lines[-num_lines:]
            content = "".join(tail).strip()
            if not content:
                return "日志为空"
            return f"📄 最近 {len(tail)} 条日志:\n\n{content}"
        except Exception as e:
            return f"读取日志失败: {e}"

    def _find_log_file(self) -> str:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        candidates = [
            os.path.join(project_root, "nohup.out"),
            os.path.join(project_root, "run.log"),
        ]
        import glob as glob_mod
        candidates.extend(sorted(glob_mod.glob(os.path.join(project_root, "logs", "*.log")), reverse=True))
        for f in candidates:
            if os.path.isfile(f) and os.path.getsize(f) > 0:
                return f
        return ""

    # ------------------------------------------------------------------
    # context
    # ------------------------------------------------------------------

    def _cmd_context(self, args: str, e_context: EventContext) -> str:
        session_id = self._get_session_id(e_context)
        agent = self._get_agent(session_id)

        sub = args.strip().lower()
        if sub == "clear":
            return self._context_clear(agent, session_id)
        else:
            return self._context_info(agent, session_id)

    def _context_info(self, agent, session_id: str) -> str:
        if not agent:
            return "⚠️ Agent 未初始化，暂无上下文信息"

        with agent.messages_lock:
            messages = agent.messages.copy()

        if not messages:
            return "当前对话上下文为空"

        user_msgs = sum(1 for m in messages if m.get("role") == "user")
        assistant_msgs = sum(1 for m in messages if m.get("role") == "assistant")
        tool_msgs = sum(1 for m in messages if m.get("role") == "tool")

        total_chars = sum(len(str(m.get("content", ""))) for m in messages)

        lines = [
            "💬 当前对话上下文",
            "",
            f"  会话: {session_id or 'default'}",
            f"  总消息数: {len(messages)}",
            f"  用户消息: {user_msgs}",
            f"  助手回复: {assistant_msgs}",
            f"  工具调用: {tool_msgs}",
            f"  内容总长度: ~{total_chars} 字符",
            "",
            "  发送 /context clear 可清除对话上下文",
        ]
        return "\n".join(lines)

    def _context_clear(self, agent, session_id: str) -> str:
        if not agent:
            return "⚠️ Agent 未初始化"

        with agent.messages_lock:
            count = len(agent.messages)
            agent.messages.clear()

        return f"✅ 已清除当前对话上下文 ({count} 条消息)"

    # ------------------------------------------------------------------
    # config
    # ------------------------------------------------------------------

    _CONFIG_WRITABLE = {
        "model",
        "agent_max_context_tokens",
        "agent_max_context_turns",
        "agent_max_steps",
    }

    _CONFIG_READABLE = _CONFIG_WRITABLE | {"channel_type"}

    def _cmd_config(self, args: str, e_context: EventContext) -> str:
        from config import conf, load_config
        import json as _json

        parts = args.strip().split(None, 1)
        if not parts:
            return self._config_show_all()

        key = parts[0].lower()
        if len(parts) == 1:
            return self._config_get(key)

        value_str = parts[1].strip()
        return self._config_set(key, value_str)

    def _config_show_all(self) -> str:
        from config import conf
        cfg = conf()
        lines = ["⚙️ 当前配置", ""]
        for key in sorted(self._CONFIG_READABLE):
            val = cfg.get(key, "")
            lines.append(f"  {key}: {val}")
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("💡 /config <key>        查看配置")
        lines.append("💡 /config <key> <val>  修改配置")
        return "\n".join(lines)

    def _config_get(self, key: str) -> str:
        from config import conf
        if key not in self._CONFIG_READABLE:
            available = ", ".join(sorted(self._CONFIG_READABLE))
            return f"不支持查看 '{key}'\n\n可查看的配置项: {available}"
        val = conf().get(key, "")
        return f"⚙️ {key}: {val}"

    def _config_set(self, key: str, value_str: str) -> str:
        from config import conf, load_config
        import json as _json

        if key not in self._CONFIG_WRITABLE:
            if key in self._CONFIG_READABLE:
                return f"⚠️ '{key}' 为只读配置，不支持修改"
            available = ", ".join(sorted(self._CONFIG_WRITABLE))
            return f"不支持修改 '{key}'\n\n可修改的配置项: {available}"

        old_val = conf().get(key, "")

        try:
            new_val = _json.loads(value_str)
        except (_json.JSONDecodeError, ValueError):
            if value_str.lower() == "true":
                new_val = True
            elif value_str.lower() == "false":
                new_val = False
            else:
                new_val = value_str

        updates = {key: new_val}

        if key == "model" and conf().get("bot_type"):
            resolved = self._resolve_bot_type_for_model(str(new_val))
            if resolved:
                updates["bot_type"] = resolved

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(project_root, "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = _json.load(f)
            file_config.update(updates)
            with open(config_path, "w", encoding="utf-8") as f:
                _json.dump(file_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            return f"写入 config.json 失败: {e}"

        try:
            load_config()
        except Exception as e:
            logger.warning(f"[CowCli] config reload warning: {e}")

        result = f"✅ 配置已更新\n\n  {key}: {old_val} → {new_val}"
        if "bot_type" in updates and updates["bot_type"] != conf().get("bot_type"):
            result += f"\n  bot_type: → {updates['bot_type']}"
        return result

    @staticmethod
    def _resolve_bot_type_for_model(model_name: str) -> str:
        """Resolve bot_type from model name, reusing AgentBridge mapping."""
        from common import const
        _EXACT = {
            "wenxin": const.BAIDU, "wenxin-4": const.BAIDU,
            "xunfei": const.XUNFEI, const.QWEN: const.QWEN,
            const.MODELSCOPE: const.MODELSCOPE,
            const.MOONSHOT: const.MOONSHOT,
            "moonshot-v1-8k": const.MOONSHOT, "moonshot-v1-32k": const.MOONSHOT,
            "moonshot-v1-128k": const.MOONSHOT,
        }
        _PREFIX = [
            ("qwen", const.QWEN_DASHSCOPE), ("qwq", const.QWEN_DASHSCOPE),
            ("qvq", const.QWEN_DASHSCOPE),
            ("gemini", const.GEMINI), ("glm", const.ZHIPU_AI),
            ("claude", const.CLAUDEAPI),
            ("moonshot", const.MOONSHOT), ("kimi", const.MOONSHOT),
            ("doubao", const.DOUBAO), ("deepseek", const.DEEPSEEK),
        ]
        if not model_name:
            return const.OPENAI
        if model_name in _EXACT:
            return _EXACT[model_name]
        if model_name.lower().startswith("minimax") or model_name in ["abab6.5-chat"]:
            return const.MiniMax
        if model_name in [const.QWEN_TURBO, const.QWEN_PLUS, const.QWEN_MAX]:
            return const.QWEN_DASHSCOPE
        for prefix, btype in _PREFIX:
            if model_name.startswith(prefix):
                return btype
        return const.OPENAI

    # ------------------------------------------------------------------
    # skill
    # ------------------------------------------------------------------

    def _cmd_skill(self, args: str, e_context: EventContext) -> str:
        parts = args.strip().split(None, 1)
        sub = parts[0].lower() if parts else ""
        sub_args = parts[1].strip() if len(parts) > 1 else ""

        if sub == "list":
            return self._skill_list(sub_args)
        elif sub == "search":
            return self._skill_search(sub_args)
        elif sub == "install":
            return self._skill_install(sub_args, e_context)
        elif sub == "uninstall":
            return self._skill_uninstall(sub_args)
        elif sub == "info":
            return self._skill_info(sub_args)
        elif sub == "enable":
            return self._skill_set_enabled(sub_args, True)
        elif sub == "disable":
            return self._skill_set_enabled(sub_args, False)
        else:
            return (
                "用法: /skill <子命令>\n\n"
                "子命令:\n"
                "  list [--remote]  查看技能列表\n"
                "  search <关键词>  搜索技能\n"
                "  install <名称>   安装技能\n"
                "  uninstall <名称> 卸载技能\n"
                "  info <名称>      查看技能详情\n"
                "  enable <名称>    启用技能\n"
                "  disable <名称>   禁用技能"
            )

    def _skill_list_local(self) -> str:
        from cli.utils import load_skills_config, get_skills_dir, get_builtin_skills_dir
        config = load_skills_config()

        if not config:
            skills_dir = get_skills_dir()
            builtin_dir = get_builtin_skills_dir()
            entries = []
            for d, source in [(builtin_dir, "builtin"), (skills_dir, "custom")]:
                if not os.path.isdir(d):
                    continue
                for name in sorted(os.listdir(d)):
                    skill_path = os.path.join(d, name)
                    if os.path.isdir(skill_path) and not name.startswith("."):
                        if os.path.exists(os.path.join(skill_path, "SKILL.md")):
                            entries.append({"name": name, "source": source, "enabled": True})
            if not entries:
                return "暂无已安装的技能\n\n💡 /skill list --remote 浏览技能广场"
            config = {e["name"]: e for e in entries}

        sorted_entries = sorted(config.values(), key=lambda e: e.get("name", ""))
        enabled_count = sum(1 for e in sorted_entries if e.get("enabled", True))

        lines = [f"📦 已安装的技能 ({enabled_count}/{len(sorted_entries)})", ""]
        for entry in sorted_entries:
            name = entry.get("name", "")
            enabled = entry.get("enabled", True)
            source = entry.get("source", "")
            icon = "✅" if enabled else "⏸️"
            desc = entry.get("description", "")
            if len(desc) > 50:
                desc = desc[:47] + "…"
            source_tag = f" · {source}" if source else ""
            line = f"{icon} {name}{source_tag}"
            if desc:
                line += f"\n   {desc}"
            lines.append(line)
            lines.append("")

        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("💡 /skill list --remote  浏览技能广场")
        lines.append("💡 /skill info <名称>     查看详情")
        return "\n".join(lines)

    def _skill_list(self, args: str) -> str:
        parts = args.strip().split()
        if "--remote" in parts or "-r" in parts:
            page = 1
            for i, p in enumerate(parts):
                if p == "--page" and i + 1 < len(parts) and parts[i + 1].isdigit():
                    page = max(1, int(parts[i + 1]))
            return self._skill_list_remote(page=page)
        return self._skill_list_local()

    _REMOTE_PAGE_SIZE = 10

    def _skill_list_remote(self, page: int = 1) -> str:
        import requests
        from cli.utils import SKILL_HUB_API, load_skills_config
        page_size = self._REMOTE_PAGE_SIZE
        try:
            resp = requests.get(
                f"{SKILL_HUB_API}/skills",
                params={"page": page, "limit": page_size},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            skills = data.get("skills", [])
            total = data.get("total", len(skills))
        except Exception as e:
            return f"获取技能广场失败: {e}"

        if not skills and page == 1:
            return "技能广场暂无可用技能"

        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages)
        installed = set(load_skills_config().keys())

        lines = [f"🌐 技能广场 (共 {total} 个技能)", ""]
        for s in skills:
            name = s.get("name", "")
            display = s.get("display_name", "") or name
            desc = s.get("description", "")
            if len(desc) > 50:
                desc = desc[:47] + "…"
            badge = " [已安装]" if name in installed else ""
            lines.append(f"📌 {display}{badge}")
            lines.append(f"   名称: {name}")
            if desc:
                lines.append(f"   {desc}")
            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"📄 第 {page}/{total_pages} 页")
        if page < total_pages:
            lines.append(f"💡 /skill list --remote --page {page + 1}  下一页")
        if page > 1:
            lines.append(f"💡 /skill list --remote --page {page - 1}  上一页")
        lines.append("💡 /skill install <名称>  安装技能")
        lines.append("💡 /skill search <关键词>  搜索技能")
        return "\n".join(lines)

    def _skill_search(self, query: str) -> str:
        if not query:
            return "请指定搜索关键词: /skill search <关键词>"

        import requests
        from cli.utils import SKILL_HUB_API, load_skills_config
        try:
            resp = requests.get(f"{SKILL_HUB_API}/skills/search", params={"q": query}, timeout=10)
            resp.raise_for_status()
            skills = resp.json().get("skills", [])
        except Exception as e:
            return f"搜索失败: {e}"

        if not skills:
            return f"未找到与「{query}」相关的技能"

        installed = set(load_skills_config().keys())
        lines = [f"🔍 搜索「{query}」({len(skills)} 个结果)", ""]
        for s in skills:
            name = s.get("name", "")
            display = s.get("display_name", "") or name
            desc = s.get("description", "")
            if len(desc) > 50:
                desc = desc[:47] + "…"
            badge = " [已安装]" if name in installed else ""
            lines.append(f"📌 {display}{badge}")
            lines.append(f"   名称: {name}")
            if desc:
                lines.append(f"   {desc}")
            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("💡 /skill install <名称>  安装技能")
        return "\n".join(lines)

    def _skill_install(self, name: str, e_context: EventContext) -> str:
        if not name:
            return "请指定要安装的技能: /skill install <名称>"

        # Run installation in a thread to avoid blocking
        # For now, invoke the CLI logic directly
        try:
            from cli.utils import get_skills_dir, SKILL_HUB_API
            import requests
            import shutil
            import zipfile
            import tempfile

            skills_dir = get_skills_dir()
            os.makedirs(skills_dir, exist_ok=True)

            if name.startswith("github:"):
                return self._skill_install_github(name[7:], skills_dir)

            resp = requests.get(f"{SKILL_HUB_API}/skills/{name}/download", timeout=15)
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "")

            if "application/json" in content_type:
                data = resp.json()
                source_type = data.get("source_type")
                if source_type == "github" or "redirect" in data:
                    source_url = data.get("source_url", "")
                    source_path = data.get("source_path")
                    return self._skill_install_github(source_url, skills_dir, subpath=source_path, skill_name=name)
                if source_type == "registry":
                    download_url = data.get("download_url")
                    if not download_url:
                        return f"此技能来自不支持的注册表，无法自动安装。"
                    from urllib.parse import urlparse
                    if urlparse(download_url).scheme != "https":
                        return "安装失败: 下载地址不安全 (非 HTTPS)"
                    provider = data.get("source_provider", "registry")
                    try:
                        dl_resp = requests.get(download_url, timeout=60, allow_redirects=True)
                        dl_resp.raise_for_status()
                    except Exception as e:
                        return f"从 {provider} 下载失败: {e}"
                    self._extract_zip(dl_resp.content, name, skills_dir)
                    self._report_install(name)
                    return f"✅ 技能 '{name}' 安装成功！"

            elif "application/zip" in content_type:
                self._extract_zip(resp.content, name, skills_dir)
                self._report_install(name)
                return f"✅ 技能 '{name}' 安装成功！"

            return "技能商店返回了未预期的响应格式"

        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return f"技能 '{name}' 未在技能商店中找到"
            return f"安装失败: {e}"
        except Exception as e:
            return f"安装失败: {e}"

    def _skill_install_github(self, spec: str, skills_dir: str,
                               subpath: str = None, skill_name: str = None) -> str:
        import requests
        import shutil
        import zipfile
        import tempfile

        if "#" in spec and not subpath:
            spec, subpath = spec.split("#", 1)
        if not skill_name:
            skill_name = subpath.rstrip("/").split("/")[-1] if subpath else spec.split("/")[-1]

        zip_url = f"https://github.com/{spec}/archive/refs/heads/main.zip"
        try:
            resp = requests.get(zip_url, timeout=60, allow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            return f"从 GitHub 下载失败: {e}"

        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = os.path.join(tmp_dir, "repo.zip")
            with open(zip_path, "wb") as f:
                f.write(resp.content)

            extract_dir = os.path.join(tmp_dir, "extracted")
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

            top_items = [d for d in os.listdir(extract_dir) if not d.startswith(".")]
            repo_root = extract_dir
            if len(top_items) == 1 and os.path.isdir(os.path.join(extract_dir, top_items[0])):
                repo_root = os.path.join(extract_dir, top_items[0])

            if subpath:
                source_dir = os.path.join(repo_root, subpath.strip("/"))
                if not os.path.isdir(source_dir):
                    return f"路径 '{subpath}' 在仓库中不存在"
            else:
                source_dir = repo_root

            target_dir = os.path.join(skills_dir, skill_name)
            if os.path.exists(target_dir):
                import shutil
                shutil.rmtree(target_dir)
            import shutil
            shutil.copytree(source_dir, target_dir)

        self._report_install(skill_name)
        return f"✅ 技能 '{skill_name}' 安装成功！"

    def _extract_zip(self, content: bytes, name: str, skills_dir: str):
        import zipfile
        import tempfile
        import shutil

        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = os.path.join(tmp_dir, "package.zip")
            with open(zip_path, "wb") as f:
                f.write(content)

            extract_dir = os.path.join(tmp_dir, "extracted")
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

            top_items = [d for d in os.listdir(extract_dir) if not d.startswith(".")]
            source = extract_dir
            if len(top_items) == 1 and os.path.isdir(os.path.join(extract_dir, top_items[0])):
                source = os.path.join(extract_dir, top_items[0])

            target = os.path.join(skills_dir, name)
            if os.path.exists(target):
                shutil.rmtree(target)
            shutil.copytree(source, target)

    def _report_install(self, name: str):
        try:
            import requests
            from cli.utils import SKILL_HUB_API
            requests.post(f"{SKILL_HUB_API}/skills/{name}/install", json={}, timeout=5)
        except Exception:
            pass

    def _skill_uninstall(self, name: str) -> str:
        if not name:
            return "请指定要卸载的技能: /skill uninstall <名称>"

        import shutil
        import json
        from cli.utils import get_skills_dir

        skills_dir = get_skills_dir()
        skill_dir = os.path.join(skills_dir, name)

        if not os.path.exists(skill_dir):
            skill_dir = self._resolve_skill_dir(name, skills_dir)

        if not skill_dir:
            return f"技能 '{name}' 未安装"

        shutil.rmtree(skill_dir)

        config_path = os.path.join(skills_dir, "skills_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                config.pop(name, None)
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
            except Exception:
                pass

        return f"✅ 技能 '{name}' 已卸载"

    @staticmethod
    def _resolve_skill_dir(name: str, skills_dir: str):
        """Find actual directory for a skill whose folder name may differ from its config name."""
        if not os.path.isdir(skills_dir):
            return None
        for entry in os.listdir(skills_dir):
            entry_path = os.path.join(skills_dir, entry)
            if not os.path.isdir(entry_path) or entry.startswith("."):
                continue
            if entry == name or entry.startswith(name + "-") or entry.endswith("-" + name):
                skill_md = os.path.join(entry_path, "SKILL.md")
                if os.path.exists(skill_md):
                    return entry_path
        return None

    @staticmethod
    def _strip_frontmatter(content: str):
        """Strip YAML frontmatter and return (metadata_dict, body)."""
        if not content.startswith("---"):
            return {}, content
        end = content.find("\n---", 3)
        if end == -1:
            return {}, content
        fm_text = content[3:end].strip()
        body = content[end + 4:].lstrip("\n")
        meta = {}
        for line in fm_text.split("\n"):
            if ":" in line:
                key, _, val = line.partition(":")
                meta[key.strip()] = val.strip().strip('"').strip("'")
        return meta, body

    def _skill_info(self, name: str) -> str:
        if not name:
            return "请指定技能名称: /skill info <名称>"

        from cli.utils import get_skills_dir, get_builtin_skills_dir

        skills_dir = get_skills_dir()
        builtin_dir = get_builtin_skills_dir()

        skill_dir = None
        source = None
        for d, src in [(skills_dir, "custom"), (builtin_dir, "builtin")]:
            candidate = os.path.join(d, name)
            if os.path.isdir(candidate):
                skill_dir = candidate
                source = src
                break

        if not skill_dir:
            resolved = self._resolve_skill_dir(name, skills_dir)
            if resolved:
                skill_dir = resolved
                source = "custom"

        if not skill_dir:
            return f"技能 '{name}' 未找到"

        skill_md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.exists(skill_md):
            return f"技能 '{name}' 没有 SKILL.md 文件"

        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()

        meta, body = self._strip_frontmatter(content)

        header_lines = [f"📖 技能: {name} [{source}]", ""]
        desc = meta.get("description", "")
        if desc:
            header_lines.append(f"  {desc}")
            header_lines.append("")

        lines = body.split("\n")
        preview = "\n".join(lines[:30])
        result = "\n".join(header_lines) + preview
        if len(lines) > 30:
            result += f"\n\n... ({len(lines) - 30} more lines)"
        return result

    def _skill_set_enabled(self, name: str, enabled: bool) -> str:
        if not name:
            action = "启用" if enabled else "禁用"
            return f"请指定技能名称: /skill {'enable' if enabled else 'disable'} <名称>"

        import json
        from cli.utils import get_skills_dir

        skills_dir = get_skills_dir()
        config_path = os.path.join(skills_dir, "skills_config.json")

        if not os.path.exists(config_path):
            return "技能配置文件不存在"

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            return f"读取配置失败: {e}"

        if name not in config:
            return f"技能 '{name}' 未在配置中找到"

        config[name]["enabled"] = enabled
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        action = "启用" if enabled else "禁用"
        icon = "✅" if enabled else "⬚"
        return f"{icon} 技能 '{name}' 已{action}"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_session_id(self, e_context: EventContext) -> str:
        context = e_context["context"]
        return context.kwargs.get("session_id") or context.get("session_id", "")

    def _get_agent(self, session_id: str):
        try:
            from bridge.bridge import Bridge
            bridge = Bridge()
            if not bridge._agent_bridge:
                return None
            return bridge._agent_bridge.get_agent(session_id=session_id or None)
        except Exception:
            return None

    def get_help_text(self, **kwargs):
        return "在对话中使用 /help 或 cow help 查看可用命令"
