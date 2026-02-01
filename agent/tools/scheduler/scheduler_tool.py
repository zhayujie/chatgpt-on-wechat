"""
Scheduler tool for creating and managing scheduled tasks
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from croniter import croniter

from agent.tools.base_tool import BaseTool, ToolResult
from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger


class SchedulerTool(BaseTool):
    """
    Tool for managing scheduled tasks (reminders, notifications, etc.)
    """
    
    name: str = "scheduler"
    description: str = (
        "创建、查询和管理定时任务。支持两种任务类型：\n"
        "1. 静态消息任务：定时发送预定义的消息\n"
        "2. 动态工具任务：定时执行工具调用并发送结果（如搜索新闻、查询天气等）\n\n"
        "使用方法：\n"
        "- 创建静态消息任务：action='create', name='任务名', message='消息内容', schedule_type='interval'/'cron'/'once', schedule_value='间隔秒数/cron表达式/时间'\n"
        "- 创建动态工具任务：action='create', name='任务名', tool_call={'tool_name': '工具名', 'tool_params': {...}, 'result_prefix': '前缀'}, schedule_type='interval'/'cron'/'once', schedule_value='值'\n"
        "- 查询列表：action='list'\n"
        "- 查看详情：action='get', task_id='任务ID'\n"
        "- 删除任务：action='delete', task_id='任务ID'\n"
        "- 启用任务：action='enable', task_id='任务ID'\n"
        "- 禁用任务：action='disable', task_id='任务ID'\n\n"
        "调度类型说明：\n"
        "- interval: 固定间隔秒数（如3600表示每小时）\n"
        "- cron: cron表达式（如'0 9 * * *'表示每天9点，'*/10 * * * *'表示每10分钟）\n"
        "- once: 一次性任务，ISO时间格式（如'2024-12-25T09:00:00'）\n\n"
        "示例：每天早上8点搜索新闻\n"
        "action='create', name='每日新闻', tool_call={'tool_name': 'bocha_search', 'tool_params': {'query': '今日新闻'}, 'result_prefix': '📰 今日新闻播报'}, schedule_type='cron', schedule_value='0 8 * * *'"
    )
    params: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "list", "get", "delete", "enable", "disable"],
                "description": "操作类型: create(创建), list(列表), get(查询), delete(删除), enable(启用), disable(禁用)"
            },
            "task_id": {
                "type": "string",
                "description": "任务ID (用于 get/delete/enable/disable 操作)"
            },
            "name": {
                "type": "string",
                "description": "任务名称 (用于 create 操作)"
            },
            "message": {
                "type": "string",
                "description": "要发送的静态消息内容 (用于 create 操作，与tool_call二选一)"
            },
            "tool_call": {
                "type": "object",
                "description": "要执行的工具调用 (用于 create 操作，与message二选一)",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "工具名称，如 'bocha_search'"
                    },
                    "tool_params": {
                        "type": "object",
                        "description": "工具参数"
                    },
                    "result_prefix": {
                        "type": "string",
                        "description": "结果前缀，如 '今日新闻：'"
                    }
                },
                "required": ["tool_name"]
            },
            "schedule_type": {
                "type": "string",
                "enum": ["cron", "interval", "once"],
                "description": "调度类型 (用于 create 操作): cron(cron表达式), interval(固定间隔秒数), once(一次性)"
            },
            "schedule_value": {
                "type": "string",
                "description": (
                    "调度值 (用于 create 操作):\n"
                    "- cron类型: cron表达式，如 '0 9 * * *' (每天9点)，'*/10 * * * *' (每10分钟)\n"
                    "- interval类型: 间隔秒数，如 '3600' (每小时)，'10' (每10秒)\n"
                    "- once类型: ISO时间，如 '2024-12-25T09:00:00'"
                )
            }
        },
        "required": ["action"]
    }
    
    def __init__(self, config: dict = None):
        super().__init__()
        self.config = config or {}
        
        # Will be set by agent bridge
        self.task_store = None
        self.current_context = None
    
    def execute(self, params: dict) -> ToolResult:
        """
        Execute scheduler operations
        
        Args:
            params: Dictionary containing:
                - action: Operation type (create/list/get/delete/enable/disable)
                - Other parameters depending on action
            
        Returns:
            ToolResult object
        """
        # Extract parameters
        action = params.get("action")
        kwargs = params
        
        if not self.task_store:
            return ToolResult.fail("错误: 定时任务系统未初始化")
        
        try:
            if action == "create":
                result = self._create_task(**kwargs)
                return ToolResult.success(result)
            elif action == "list":
                result = self._list_tasks(**kwargs)
                return ToolResult.success(result)
            elif action == "get":
                result = self._get_task(**kwargs)
                return ToolResult.success(result)
            elif action == "delete":
                result = self._delete_task(**kwargs)
                return ToolResult.success(result)
            elif action == "enable":
                result = self._enable_task(**kwargs)
                return ToolResult.success(result)
            elif action == "disable":
                result = self._disable_task(**kwargs)
                return ToolResult.success(result)
            else:
                return ToolResult.fail(f"未知操作: {action}")
        except Exception as e:
            logger.error(f"[SchedulerTool] Error: {e}")
            return ToolResult.fail(f"操作失败: {str(e)}")
    
    def _create_task(self, **kwargs) -> str:
        """Create a new scheduled task"""
        name = kwargs.get("name")
        message = kwargs.get("message")
        tool_call = kwargs.get("tool_call")
        schedule_type = kwargs.get("schedule_type")
        schedule_value = kwargs.get("schedule_value")
        
        # Validate required fields
        if not name:
            return "错误: 缺少任务名称 (name)"
        if not message and not tool_call:
            return "错误: 必须提供 message 或 tool_call 之一"
        if message and tool_call:
            return "错误: message 和 tool_call 不能同时提供，请选择其一"
        if not schedule_type:
            return "错误: 缺少调度类型 (schedule_type)"
        if not schedule_value:
            return "错误: 缺少调度值 (schedule_value)"
        
        # Validate schedule
        schedule = self._parse_schedule(schedule_type, schedule_value)
        if not schedule:
            return f"错误: 无效的调度配置 - type: {schedule_type}, value: {schedule_value}"
        
        # Get context info for receiver
        if not self.current_context:
            return "错误: 无法获取当前对话上下文"
        
        context = self.current_context
        
        # Create task
        task_id = str(uuid.uuid4())[:8]
        
        # Build action based on message or tool_call
        if message:
            action = {
                "type": "send_message",
                "content": message,
                "receiver": context.get("receiver"),
                "receiver_name": self._get_receiver_name(context),
                "is_group": context.get("isgroup", False),
                "channel_type": self.config.get("channel_type", "unknown")
            }
        else:  # tool_call
            action = {
                "type": "tool_call",
                "tool_name": tool_call.get("tool_name"),
                "tool_params": tool_call.get("tool_params", {}),
                "result_prefix": tool_call.get("result_prefix", ""),
                "receiver": context.get("receiver"),
                "receiver_name": self._get_receiver_name(context),
                "is_group": context.get("isgroup", False),
                "channel_type": self.config.get("channel_type", "unknown")
            }
        
        task = {
            "id": task_id,
            "name": name,
            "enabled": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "schedule": schedule,
            "action": action
        }
        
        # Calculate initial next_run_at
        next_run = self._calculate_next_run(task)
        if next_run:
            task["next_run_at"] = next_run.isoformat()
        
        # Save task
        self.task_store.add_task(task)
        
        # Format response
        schedule_desc = self._format_schedule_description(schedule)
        receiver_desc = task["action"]["receiver_name"] or task["action"]["receiver"]
        
        if message:
            content_desc = f"💬 消息: {message}"
        else:
            tool_name = tool_call.get("tool_name")
            tool_params_str = str(tool_call.get("tool_params", {}))
            prefix = tool_call.get("result_prefix", "")
            content_desc = f"🔧 工具调用: {tool_name}({tool_params_str})"
            if prefix:
                content_desc += f"\n📝 结果前缀: {prefix}"
        
        return (
            f"✅ 定时任务创建成功\n\n"
            f"📋 任务ID: {task_id}\n"
            f"📝 名称: {name}\n"
            f"⏰ 调度: {schedule_desc}\n"
            f"👤 接收者: {receiver_desc}\n"
            f"{content_desc}\n"
            f"🕐 下次执行: {next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else '未知'}"
        )
    
    def _list_tasks(self, **kwargs) -> str:
        """List all tasks"""
        tasks = self.task_store.list_tasks()
        
        if not tasks:
            return "📋 暂无定时任务"
        
        lines = [f"📋 定时任务列表 (共 {len(tasks)} 个)\n"]
        
        for task in tasks:
            status = "✅" if task.get("enabled", True) else "❌"
            schedule_desc = self._format_schedule_description(task.get("schedule", {}))
            next_run = task.get("next_run_at")
            next_run_str = datetime.fromisoformat(next_run).strftime('%m-%d %H:%M') if next_run else "未知"
            
            lines.append(
                f"{status} [{task['id']}] {task['name']}\n"
                f"   ⏰ {schedule_desc} | 下次: {next_run_str}"
            )
        
        return "\n".join(lines)
    
    def _get_task(self, **kwargs) -> str:
        """Get task details"""
        task_id = kwargs.get("task_id")
        if not task_id:
            return "错误: 缺少任务ID (task_id)"
        
        task = self.task_store.get_task(task_id)
        if not task:
            return f"错误: 任务 '{task_id}' 不存在"
        
        status = "启用" if task.get("enabled", True) else "禁用"
        schedule_desc = self._format_schedule_description(task.get("schedule", {}))
        action = task.get("action", {})
        next_run = task.get("next_run_at")
        next_run_str = datetime.fromisoformat(next_run).strftime('%Y-%m-%d %H:%M:%S') if next_run else "未知"
        last_run = task.get("last_run_at")
        last_run_str = datetime.fromisoformat(last_run).strftime('%Y-%m-%d %H:%M:%S') if last_run else "从未执行"
        
        return (
            f"📋 任务详情\n\n"
            f"ID: {task['id']}\n"
            f"名称: {task['name']}\n"
            f"状态: {status}\n"
            f"调度: {schedule_desc}\n"
            f"接收者: {action.get('receiver_name', action.get('receiver'))}\n"
            f"消息: {action.get('content')}\n"
            f"下次执行: {next_run_str}\n"
            f"上次执行: {last_run_str}\n"
            f"创建时间: {datetime.fromisoformat(task['created_at']).strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    def _delete_task(self, **kwargs) -> str:
        """Delete a task"""
        task_id = kwargs.get("task_id")
        if not task_id:
            return "错误: 缺少任务ID (task_id)"
        
        task = self.task_store.get_task(task_id)
        if not task:
            return f"错误: 任务 '{task_id}' 不存在"
        
        self.task_store.delete_task(task_id)
        return f"✅ 任务 '{task['name']}' ({task_id}) 已删除"
    
    def _enable_task(self, **kwargs) -> str:
        """Enable a task"""
        task_id = kwargs.get("task_id")
        if not task_id:
            return "错误: 缺少任务ID (task_id)"
        
        task = self.task_store.get_task(task_id)
        if not task:
            return f"错误: 任务 '{task_id}' 不存在"
        
        self.task_store.enable_task(task_id, True)
        return f"✅ 任务 '{task['name']}' ({task_id}) 已启用"
    
    def _disable_task(self, **kwargs) -> str:
        """Disable a task"""
        task_id = kwargs.get("task_id")
        if not task_id:
            return "错误: 缺少任务ID (task_id)"
        
        task = self.task_store.get_task(task_id)
        if not task:
            return f"错误: 任务 '{task_id}' 不存在"
        
        self.task_store.enable_task(task_id, False)
        return f"✅ 任务 '{task['name']}' ({task_id}) 已禁用"
    
    def _parse_schedule(self, schedule_type: str, schedule_value: str) -> Optional[dict]:
        """Parse and validate schedule configuration"""
        try:
            if schedule_type == "cron":
                # Validate cron expression
                croniter(schedule_value)
                return {"type": "cron", "expression": schedule_value}
            
            elif schedule_type == "interval":
                # Parse interval in seconds
                seconds = int(schedule_value)
                if seconds <= 0:
                    return None
                return {"type": "interval", "seconds": seconds}
            
            elif schedule_type == "once":
                # Parse datetime
                datetime.fromisoformat(schedule_value)
                return {"type": "once", "run_at": schedule_value}
            
        except Exception as e:
            logger.error(f"[SchedulerTool] Invalid schedule: {e}")
            return None
        
        return None
    
    def _calculate_next_run(self, task: dict) -> Optional[datetime]:
        """Calculate next run time for a task"""
        schedule = task.get("schedule", {})
        schedule_type = schedule.get("type")
        now = datetime.now()
        
        if schedule_type == "cron":
            expression = schedule.get("expression")
            cron = croniter(expression, now)
            return cron.get_next(datetime)
        
        elif schedule_type == "interval":
            seconds = schedule.get("seconds", 0)
            from datetime import timedelta
            return now + timedelta(seconds=seconds)
        
        elif schedule_type == "once":
            run_at_str = schedule.get("run_at")
            return datetime.fromisoformat(run_at_str)
        
        return None
    
    def _format_schedule_description(self, schedule: dict) -> str:
        """Format schedule as human-readable description"""
        schedule_type = schedule.get("type")
        
        if schedule_type == "cron":
            expr = schedule.get("expression", "")
            # Try to provide friendly description
            if expr == "0 9 * * *":
                return "每天 9:00"
            elif expr == "0 */1 * * *":
                return "每小时"
            elif expr == "*/30 * * * *":
                return "每30分钟"
            else:
                return f"Cron: {expr}"
        
        elif schedule_type == "interval":
            seconds = schedule.get("seconds", 0)
            if seconds >= 86400:
                days = seconds // 86400
                return f"每 {days} 天"
            elif seconds >= 3600:
                hours = seconds // 3600
                return f"每 {hours} 小时"
            elif seconds >= 60:
                minutes = seconds // 60
                return f"每 {minutes} 分钟"
            else:
                return f"每 {seconds} 秒"
        
        elif schedule_type == "once":
            run_at = schedule.get("run_at", "")
            try:
                dt = datetime.fromisoformat(run_at)
                return f"一次性 ({dt.strftime('%Y-%m-%d %H:%M')})"
            except:
                return "一次性"
        
        return "未知"
    
    def _get_receiver_name(self, context: Context) -> str:
        """Get receiver name from context"""
        try:
            msg = context.get("msg")
            if msg:
                if context.get("isgroup"):
                    return msg.other_user_nickname or "群聊"
                else:
                    return msg.from_user_nickname or "用户"
        except:
            pass
        return "未知"
