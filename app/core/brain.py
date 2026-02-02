import re
import logging
from app.database.session import AsyncSessionLocal
from app.database import crud

logger = logging.getLogger(__name__)

class JulesBrain:
    """
    Interprets natural language or structured commands to execute system actions.
    """

    async def process_text(self, text: str):
        """
        Parses the text and determines the action.
        Returns a response string.
        """
        text = text.strip()

        # Simple Command Parsing (Rule-based)
        if text.startswith("/add"):
            return await self._handle_add(text)
        elif text.startswith("/list"):
            return await self._handle_list()
        elif text.startswith("/del"):
            return await self._handle_del(text)
        elif text.startswith("/help"):
             return self._handle_help()

        # Fallback for now (AI expansion point)
        return "I didn't understand that command. Try /help."

    async def _handle_add(self, text: str):
        """
        Parses /add with key:value lines or naive natural language.
        Format:
        /add
        source: @src
        target: @tgt
        ...
        """
        lines = text.splitlines()
        task_data = {}

        # Skip the first line if it's just /add
        start_idx = 1 if lines[0].strip() == "/add" else 0

        for line in lines[start_idx:]:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                if key in ['source', 'target', 'find_user', 'replace_user', 'find_link', 'replace_link']:
                    task_data[key] = value

        if 'source' not in task_data or 'target' not in task_data:
            return "❌ Error: `source` and `target` are required fields."

        async with AsyncSessionLocal() as session:
            await crud.create_task(
                session,
                source=task_data['source'],
                target=task_data['target'],
                find_user=task_data.get('find_user'),
                replace_user=task_data.get('replace_user'),
                find_link=task_data.get('find_link'),
                replace_link=task_data.get('replace_link')
            )

        return f"✅ Task added: {task_data['source']} -> {task_data['target']}"

    async def _handle_list(self):
        async with AsyncSessionLocal() as session:
            tasks = await crud.get_all_tasks(session)

        if not tasks:
            return "No active tasks found."

        msg = "**📋 Active Tasks:**\n\n"
        for t in tasks:
            msg += (
                f"**ID: {t.id}**\n"
                f"Source: `{t.source}`\n"
                f"Target: `{t.target}`\n"
            )
            if t.find_user:
                 msg += f"User: `{t.find_user}` -> `{t.replace_user}`\n"
            if t.find_link:
                 msg += f"Link: `{t.find_link}` -> `{t.replace_link}`\n"
            msg += "-------------------\n"
        return msg

    async def _handle_del(self, text: str):
        try:
            # Expected: /del <ID>
            parts = text.split()
            if len(parts) < 2:
                return "❌ Usage: `/del <ID>`"

            task_id = int(parts[1])
            async with AsyncSessionLocal() as session:
                await crud.delete_task(session, task_id)
            return f"✅ Deleted task ID: {task_id}"
        except ValueError:
            return "❌ Invalid ID format."
        except Exception as e:
            return f"❌ Error deleting task: {e}"

    def _handle_help(self):
        return (
            "**🤖 Jules Help**\n\n"
            "`/list` - List tasks\n"
            "`/del <ID>` - Delete task\n"
            "`/add` - Add task (multi-line format supported)\n"
            "   source: @src\n"
            "   target: @tgt"
        )
