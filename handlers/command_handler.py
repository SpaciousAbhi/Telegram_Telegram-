from telethon import events
from config_state import get_cached_config, update_cached_config
from utils import join_channel

async def command_handler(event):
    """
    Handles commands sent to 'Saved Messages'.
    """
    text = event.raw_text

    if text.startswith('/help'):
        help_text = (
            "**🤖 Userbot Commands**\n\n"
            "`/list` - List all active tasks\n"
            "`/del <ID>` - Delete a task by ID\n"
            "`/add` - Add a new task (see template below)\n\n"
            "**Add Task Template:**\n"
            "```\n"
            "/add\n"
            "source: @SourceChannel\n"
            "target: @TargetChannel\n"
            "find_user: @OldUser (optional)\n"
            "replace_user: @NewUser (optional)\n"
            "find_link: t.me/OldLink (optional)\n"
            "replace_link: t.me/NewLink (optional)\n"
            "```"
        )
        await event.reply(help_text)
        return

    if text.startswith('/list'):
        config = await get_cached_config(event.client)
        tasks = config.get('tasks', [])

        if not tasks:
            await event.reply("No active tasks found.")
            return

        msg = "**📋 Active Tasks:**\n\n"
        for i, task in enumerate(tasks):
            msg += (
                f"**ID: {i}**\n"
                f"Source: `{task.get('source')}`\n"
                f"Target: `{task.get('target')}`\n"
                f"Find/Rep User: `{task.get('find_user', 'N/A')}` -> `{task.get('replace_user', 'N/A')}`\n"
                f"Find/Rep Link: `{task.get('find_link', 'N/A')}` -> `{task.get('replace_link', 'N/A')}`\n"
                "-------------------\n"
            )
        await event.reply(msg)
        return

    if text.startswith('/del'):
        try:
            _, task_id = text.split(maxsplit=1)
            task_id = int(task_id)

            config = await get_cached_config(event.client)
            tasks = config.get('tasks', [])

            if 0 <= task_id < len(tasks):
                removed = tasks.pop(task_id)
                await update_cached_config(event.client, config)
                await event.reply(f"✅ Deleted task for source: `{removed.get('source')}`")
            else:
                await event.reply("❌ Invalid Task ID.")

        except ValueError:
            await event.reply("❌ Usage: `/del <ID>`")
        return

    if text.startswith('/add'):
        lines = text.splitlines()
        task = {}

        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()

                if key in ['source', 'target', 'find_user', 'replace_user', 'find_link', 'replace_link']:
                    task[key] = value

        # Validation
        if 'source' not in task or 'target' not in task:
            await event.reply("❌ Error: `source` and `target` are required.")
            return

        # Try to join source
        joined = await join_channel(event.client, task['source'])
        if not joined:
            await event.reply(f"⚠️ Warning: Could not join `{task['source']}`. Monitoring might not work if you are not a member.")

        # Save
        config = await get_cached_config(event.client)
        if 'tasks' not in config:
            config['tasks'] = []

        config['tasks'].append(task)
        await update_cached_config(event.client, config)

        await event.reply(f"✅ Task added!\nMonitoring: `{task['source']}` -> `{task['target']}`")
        return
