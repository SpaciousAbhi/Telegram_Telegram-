import asyncio
import logging
from telethon import events
from app.database.db import get_db
from app.database.models import Task, AppLog, GlobalSettings
from app.core.transformer import ContentTransformer
import json

logger = logging.getLogger(__name__)

async def process_message(client, event, task):
    """
    Core forwarding logic for a single task and message.
    """
    try:
        # Fetch Global Rules
        global_rules = []
        log_channel = None

        with get_db() as db:
            # Re-fetch task to avoid stale state
            current_task = db.query(Task).filter(Task.id == task.id).first()
            if not current_task: return # Task deleted

            # Get Rules
            setting_rules = db.query(GlobalSettings).filter(GlobalSettings.key == 'replacements').first()
            if setting_rules and setting_rules.value:
                global_rules = json.loads(setting_rules.value)

            # Get Log Channel
            setting_log = db.query(GlobalSettings).filter(GlobalSettings.key == 'log_channel').first()
            if setting_log and setting_log.value:
                log_channel = json.loads(setting_log.value)

            # Update ID happens later

        # 1. Transform Content
        modified_text, changes = ContentTransformer.apply_replacements(
            event.text,
            event.entities,
            task.config,
            global_settings=global_rules
        )

        # 2. Forward (Send as new message to avoid "Forwarded from" if desired,
        # or use actual forward. Here we use send_message for cleaner output)
        if event.media:
            await client.send_file(task.target_id, event.media, caption=modified_text)
        else:
            await client.send_message(task.target_id, modified_text)

        # 3. Update State (Last Processed ID)
        # Note: In a real high-concurrency DB, we might want to batch this.
        with get_db() as db:
            # Re-fetch task to avoid stale state
            current_task = db.query(Task).filter(Task.id == task.id).first()
            if current_task:
                current_task.last_processed_id = event.id
                db.commit()

        # 4. Log Success
        log_msg = f"Task {task.id}: Forwarded Msg {event.id}. Changes: {changes}"
        logger.info(log_msg)

        # Send to Log Channel
        if log_channel:
            try:
                # Format a nice report
                changes_text = "\n".join([f"🔹 {c}" for c in changes]) if changes else "No changes."
                report = (
                    f"**🔄 Forward Report**\n"
                    f"**Source:** {task.source_title}\n"
                    f"**Target:** {task.target_title}\n"
                    f"**Msg ID:** `{event.id}`\n\n"
                    f"**Actions:**\n{changes_text}"
                )
                await client.send_message(log_channel, report, link_preview=False)
            except Exception as e:
                logger.error(f"Failed to send log to channel: {e}")

    except Exception as e:
        logger.error(f"Task {task.id}: Failed to forward Msg {event.id}: {e}")
        # Update Error Count
        with get_db() as db:
             current_task = db.query(Task).filter(Task.id == task.id).first()
             if current_task:
                 current_task.error_count += 1
                 db.commit()


@events.register(events.NewMessage(incoming=True))
async def live_monitor(event):
    """
    Listens for new messages and routes them to active tasks.
    """
    # optimization: check if chat_id matches any active source in DB (cached)
    chat_id = event.chat_id

    # For now, we query DB. In prod, cache active sources in memory.
    with get_db() as db:
        # We need to match by ID or Username.
        # Telethon event.chat_id is integer. Source in DB might be username or int.
        # This matching logic needs to be robust.
        # For this prototype, we assume we can resolve the entity.

        # Helper: Try to find tasks where source matches this event
        # (This is tricky without exact ID matching, assumes source_id is int or we resolve it)
        # For simplicity in this step, let's assume we match roughly.

        # Fetch all active live tasks
        tasks = db.query(Task).filter(Task.is_active == True, Task.mode == 'live').all()

        matching_tasks = []
        for t in tasks:
            # Check if this event comes from the task source
            # We compare InputChannel IDs or Usernames
            try:
                # We can't easily compare strings to IDs without a cache or get_entity.
                # A robust way is to rely on the userbot knowing the ID.
                # For this implementation, we will check if the event.chat matches.
                sender = await event.get_chat()
                sender_id = str(sender.id)
                sender_username = f"@{sender.username}" if sender.username else ""

                if str(t.source_id) == sender_id or (sender_username and t.source_id.lower() == sender_username.lower()):
                    matching_tasks.append(t)
            except Exception:
                continue

        if not matching_tasks:
            return

        # Execute
        for task in matching_tasks:
             await process_message(event.client, event, task)
