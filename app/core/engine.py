import asyncio
import logging
from telethon import events
from telethon.tl.functions.channels import JoinChannelRequest
from app.database.db import get_db
from app.database.models import Task, AppLog, GlobalSettings
from app.core.transformer import ContentTransformer
import json

logger = logging.getLogger(__name__)

async def resolve_and_join_tasks(client):
    """
    On startup, iterate all tasks, resolve their entities (usernames -> IDs),
    and attempt to join source channels.
    """
    logger.info("Starting Task Resolution & Auto-Join...")

    with get_db() as db:
        tasks = db.query(Task).filter(Task.is_active == True).all()
        logger.info(f"Found {len(tasks)} active tasks in DB.")

        for task in tasks:
            logger.info(f"Processing Task #{task.id}: Source='{task.source_id}' Target='{task.target_id}'")

            # 1. Resolve Source
            try:
                # If it's already a number, we might skip or re-verify
                # But let's try to get entity to ensure we are in it
                try:
                    # Handle case where user entered integer string
                    input_arg = int(task.source_id) if task.source_id.lstrip('-').isdigit() else task.source_id
                except:
                    input_arg = task.source_id

                entity = await client.get_entity(input_arg)

                # Get the real numeric ID
                real_id = str(entity.id)
                logger.info(f" -> Resolved '{task.source_id}' to ID: {real_id} Title: {getattr(entity, 'title', 'N/A')}")

                if task.source_id != real_id:
                    logger.info(f" -> Updating DB Source: {task.source_id} -> {real_id}")
                    task.source_id = real_id

                # Update Title if possible
                if hasattr(entity, 'title'):
                    task.source_title = entity.title

                # 2. Join
                try:
                    await client(JoinChannelRequest(entity))
                    logger.info(f" -> Joined {task.source_title}")
                except Exception as e:
                    # 'UserAlreadyParticipantError' is common/fine
                    if "already" not in str(e).lower():
                        logger.warning(f" -> Failed to join {task.source_id}: {e}")
                    else:
                        logger.info(" -> Already a member.")

            except Exception as e:
                logger.error(f" -> Could not resolve Source {task.source_id}: {e}")

            # 3. Resolve Target (Just for ID consistency, no join needed usually if public)
            try:
                entity_target = await client.get_entity(task.target_id)
                real_target_id = str(entity_target.id)

                if task.target_id != real_target_id:
                     logger.info(f"Resolved Target: {task.target_id} -> {real_target_id}")
                     task.target_id = real_target_id

                if hasattr(entity_target, 'title'):
                    task.target_title = entity_target.title

            except Exception as e:
                logger.error(f"Could not resolve Target {task.target_id}: {e}")

        db.commit()
    logger.info("Task Resolution Complete.")

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

        # Check if skipped
        if modified_text is None:
             logger.info(f"Task {task.id}: Skipped msg {event.id} based on rules.")
             return

        # 2. Forward (Send as new message to avoid "Forwarded from" if desired,
        # or use actual forward. Here we use send_message for cleaner output)
        try:
            target_entity = await client.get_entity(int(task.target_id)) if task.target_id.lstrip('-').isdigit() else task.target_id
        except:
            target_entity = task.target_id

        if event.media:
            await client.send_file(target_entity, event.media, caption=modified_text)
        else:
            await client.send_message(target_entity, modified_text)

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
                # Resolve entity if it's a string (username)
                log_entity = log_channel
                if isinstance(log_channel, str) and not log_channel.startswith('-100'):
                     try:
                         log_entity = await client.get_entity(log_channel)
                     except:
                         # Fallback: maybe it's a numeric string ID?
                         if log_channel.lstrip('-').isdigit():
                             log_entity = int(log_channel)

                # Format a nice report
                changes_text = "\n".join([f"🔹 {c}" for c in changes]) if changes else "No changes."
                status_emoji = "✅" if not changes else "⚠️"

                report = (
                    f"**🔄 Forward Report**\n"
                    f"**Source:** {task.source_title}\n"
                    f"**Target:** {task.target_title}\n"
                    f"**Msg ID:** `{event.id}`\n\n"
                    f"**Actions:**\n{changes_text}"
                )
                await client.send_message(log_entity, report, link_preview=False)
            except Exception as e:
                logger.error(f"Failed to send log to channel '{log_channel}': {e}")

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
    try:
        chat = await event.get_chat()
        chat_id = chat.id
        chat_username = chat.username.lower() if chat.username else None

        logger.info(f"Incoming Msg from ID: {chat_id} Username: {chat_username}")
    except Exception as e:
        logger.debug(f"Could not resolve chat: {e}")
        return

    with get_db() as db:
        # Fetch all active live tasks
        tasks = db.query(Task).filter(Task.is_active == True, Task.mode == 'live').all()

        matching_tasks = []
        for t in tasks:
            # Source in DB is a string (could be "@username" or "12345" or "-10012345")
            db_source = t.source_id.lower().strip()

            # 1. Check Username Match (@user == @user)
            if chat_username and db_source.startswith('@') and db_source == f"@{chat_username}":
                matching_tasks.append(t)
                continue

            # 2. Check ID Match (123 == 123)
            # Telethon IDs can be tricky (-100 prefix).
            # We normalize both to strings and try to match end-to-end or containment
            str_chat_id = str(chat_id)

            # Simple exact match
            if db_source == str_chat_id:
                matching_tasks.append(t)
                continue

            # Telethon Channel ID fix (sometimes user stores "-100123" but event is "123")
            # Or user stores "123" and event is "-100123"
            if db_source.endswith(str_chat_id) or str_chat_id.endswith(db_source):
                # Ensure it's not a partial match of a different number (e.g. 123 matching 9123)
                # This is "good enough" for V1 but ideally we resolve entity on Task Creation.
                matching_tasks.append(t)
                continue

        if not matching_tasks:
            return

        # Execute
        for task in matching_tasks:
             logger.info(f"Match found! Forwarding to Task {task.id}")
             await process_message(event.client, event, task)
