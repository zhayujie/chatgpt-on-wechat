"""
Integration module for scheduler with AgentBridge
"""

import os
from typing import Optional
from config import conf
from common.log import logger
from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType

# Global scheduler service instance
_scheduler_service = None
_task_store = None


def init_scheduler(agent_bridge) -> bool:
    """
    Initialize scheduler service
    
    Args:
        agent_bridge: AgentBridge instance
        
    Returns:
        True if initialized successfully
    """
    global _scheduler_service, _task_store
    
    try:
        from agent.tools.scheduler.task_store import TaskStore
        from agent.tools.scheduler.scheduler_service import SchedulerService
        
        # Get workspace from config
        workspace_root = os.path.expanduser(conf().get("agent_workspace", "~/cow"))
        store_path = os.path.join(workspace_root, "scheduler", "tasks.json")
        
        # Create task store
        _task_store = TaskStore(store_path)
        logger.info(f"[Scheduler] Task store initialized: {store_path}")
        
        # Create execute callback
        def execute_task_callback(task: dict):
            """Callback to execute a scheduled task"""
            try:
                action = task.get("action", {})
                action_type = action.get("type")
                
                if action_type == "send_message":
                    _execute_send_message(task, agent_bridge)
                elif action_type == "tool_call":
                    _execute_tool_call(task, agent_bridge)
                else:
                    logger.warning(f"[Scheduler] Unknown action type: {action_type}")
            except Exception as e:
                logger.error(f"[Scheduler] Error executing task {task.get('id')}: {e}")
        
        # Create scheduler service
        _scheduler_service = SchedulerService(_task_store, execute_task_callback)
        _scheduler_service.start()
        
        logger.info("[Scheduler] Scheduler service initialized and started")
        return True
        
    except Exception as e:
        logger.error(f"[Scheduler] Failed to initialize scheduler: {e}")
        return False


def get_task_store():
    """Get the global task store instance"""
    return _task_store


def get_scheduler_service():
    """Get the global scheduler service instance"""
    return _scheduler_service


def _execute_send_message(task: dict, agent_bridge):
    """
    Execute a send_message action
    
    Args:
        task: Task dictionary
        agent_bridge: AgentBridge instance
    """
    try:
        action = task.get("action", {})
        content = action.get("content", "")
        receiver = action.get("receiver")
        is_group = action.get("is_group", False)
        channel_type = action.get("channel_type", "unknown")
        
        if not receiver:
            logger.error(f"[Scheduler] Task {task['id']}: No receiver specified")
            return
        
        # Create context for sending message
        context = Context(ContextType.TEXT, content)
        context["receiver"] = receiver
        context["isgroup"] = is_group
        context["session_id"] = receiver
        
        # Channel-specific context setup
        if channel_type == "web":
            # Web channel needs request_id
            import uuid
            request_id = f"scheduler_{task['id']}_{uuid.uuid4().hex[:8]}"
            context["request_id"] = request_id
            logger.debug(f"[Scheduler] Generated request_id for web channel: {request_id}")
        elif channel_type == "feishu":
            # Feishu channel: for scheduled tasks, send as new message (no msg_id to reply to)
            # Use chat_id for groups, open_id for private chats
            context["receive_id_type"] = "chat_id" if is_group else "open_id"
            # Keep isgroup as is, but set msg to None (no original message to reply to)
            # Feishu channel will detect this and send as new message instead of reply
            context["msg"] = None
            logger.debug(f"[Scheduler] Feishu: receive_id_type={context['receive_id_type']}, is_group={is_group}, receiver={receiver}")
        
        # Create reply
        reply = Reply(ReplyType.TEXT, content)
        
        # Get channel and send
        from channel.channel_factory import create_channel
        
        try:
            channel = create_channel(channel_type)
            if channel:
                # For web channel, register the request_id to session mapping
                if channel_type == "web" and hasattr(channel, 'request_to_session'):
                    channel.request_to_session[request_id] = receiver
                    logger.debug(f"[Scheduler] Registered request_id {request_id} -> session {receiver}")
                
                channel.send(reply, context)
                logger.info(f"[Scheduler] Task {task['id']} executed: sent message to {receiver}")
            else:
                logger.error(f"[Scheduler] Failed to create channel: {channel_type}")
        except Exception as e:
            logger.error(f"[Scheduler] Failed to send message: {e}")
            import traceback
            logger.error(f"[Scheduler] Traceback: {traceback.format_exc()}")
            
    except Exception as e:
        logger.error(f"[Scheduler] Error in _execute_send_message: {e}")
        import traceback
        logger.error(f"[Scheduler] Traceback: {traceback.format_exc()}")


def _execute_tool_call(task: dict, agent_bridge):
    """
    Execute a tool_call action
    
    Args:
        task: Task dictionary
        agent_bridge: AgentBridge instance
    """
    try:
        action = task.get("action", {})
        tool_name = action.get("tool_name")
        tool_params = action.get("tool_params", {})
        result_prefix = action.get("result_prefix", "")
        receiver = action.get("receiver")
        is_group = action.get("is_group", False)
        channel_type = action.get("channel_type", "unknown")
        
        if not tool_name:
            logger.error(f"[Scheduler] Task {task['id']}: No tool_name specified")
            return
        
        if not receiver:
            logger.error(f"[Scheduler] Task {task['id']}: No receiver specified")
            return
        
        # Get tool manager and create tool instance
        from agent.tools.tool_manager import ToolManager
        tool_manager = ToolManager()
        tool = tool_manager.create_tool(tool_name)
        
        if not tool:
            logger.error(f"[Scheduler] Task {task['id']}: Tool '{tool_name}' not found")
            return
        
        # Execute tool
        logger.info(f"[Scheduler] Task {task['id']}: Executing tool '{tool_name}' with params {tool_params}")
        result = tool.execute(tool_params)
        
        # Get result content
        if hasattr(result, 'result'):
            content = result.result
        else:
            content = str(result)
        
        # Add prefix if specified
        if result_prefix:
            content = f"{result_prefix}\n\n{content}"
        
        # Send result as message
        context = Context(ContextType.TEXT, content)
        context["receiver"] = receiver
        context["isgroup"] = is_group
        context["session_id"] = receiver
        
        # Channel-specific context setup
        if channel_type == "web":
            # Web channel needs request_id
            import uuid
            request_id = f"scheduler_{task['id']}_{uuid.uuid4().hex[:8]}"
            context["request_id"] = request_id
            logger.debug(f"[Scheduler] Generated request_id for web channel: {request_id}")
        elif channel_type == "feishu":
            # Feishu channel: for scheduled tasks, send as new message (no msg_id to reply to)
            context["receive_id_type"] = "chat_id" if is_group else "open_id"
            context["msg"] = None
            logger.debug(f"[Scheduler] Feishu: receive_id_type={context['receive_id_type']}, is_group={is_group}, receiver={receiver}")
        
        reply = Reply(ReplyType.TEXT, content)
        
        # Get channel and send
        from channel.channel_factory import create_channel
        
        try:
            channel = create_channel(channel_type)
            if channel:
                # For web channel, register the request_id to session mapping
                if channel_type == "web" and hasattr(channel, 'request_to_session'):
                    channel.request_to_session[request_id] = receiver
                    logger.debug(f"[Scheduler] Registered request_id {request_id} -> session {receiver}")
                
                channel.send(reply, context)
                logger.info(f"[Scheduler] Task {task['id']} executed: sent tool result to {receiver}")
            else:
                logger.error(f"[Scheduler] Failed to create channel: {channel_type}")
        except Exception as e:
            logger.error(f"[Scheduler] Failed to send tool result: {e}")
            
    except Exception as e:
        logger.error(f"[Scheduler] Error in _execute_tool_call: {e}")


def attach_scheduler_to_tool(tool, context: Context = None):
    """
    Attach scheduler components to a SchedulerTool instance
    
    Args:
        tool: SchedulerTool instance
        context: Current context (optional)
    """
    if _task_store:
        tool.task_store = _task_store
    
    if context:
        tool.current_context = context
        
        # Also set channel_type from config
        channel_type = conf().get("channel_type", "unknown")
        if not tool.config:
            tool.config = {}
        tool.config["channel_type"] = channel_type
