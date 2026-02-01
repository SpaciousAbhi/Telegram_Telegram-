from telethon import events, Button
from app.ui.menu_builder import MenuBuilder
from app.ui.settings_menu import SettingsMenu
from app.ui.state_machine import StateMachine
from app.database.db import get_db
from app.database.models import Task, GlobalSettings
import logging
import json

logger = logging.getLogger(__name__)

async def handle_create_task(event):
    """Start the task creation wizard."""
    user_id = event.sender_id
    StateMachine.clear_state(user_id)
    StateMachine.set_step(user_id, 'awaiting_source')

    await event.edit(
        "**🆕 New Task: Step 1/3**\n\n"
        "Please send the **Source Channel** (Username, ID, or Link).\n"
        "The bot must be a member of this channel.",
        buttons=MenuBuilder.cancel_button()
    )

async def handle_save_task(event, user_id):
    """Finalize and save the task to DB."""
    state = StateMachine.get_state(user_id)

    with get_db() as db:
        new_task = Task(
            source_id=state.get('source'),
            source_title=state.get('source_title', 'Unknown Source'),
            target_id=state.get('target'),
            target_title=state.get('target_title', 'Unknown Target'),
            config=state.get('config', {}),
            mode='live', # Defaulting to live for now
            is_active=True
        )
        db.add(new_task)
        db.commit()

    StateMachine.clear_state(user_id)
    await event.edit(
        "**✅ Task Created Successfully!**\n\n"
        "The bot is now monitoring the source.",
        buttons=MenuBuilder.main_menu()
    )

@events.register(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()
    user_id = event.sender_id

    # --- Navigation ---
    if data == 'create_task':
        await handle_create_task(event)
        return

    if data == 'cancel_action' or data == 'back_to_main':
        StateMachine.clear_state(user_id)
        await event.edit("**🤖 Ultimate Forwarder Bot**", buttons=MenuBuilder.main_menu())
        return

    # --- Settings Menu ---
    if data == 'settings':
        await event.edit("**⚙️ Global Settings**", buttons=SettingsMenu.get_settings_menu())
        return

    if data == 'settings_log_channel':
        StateMachine.set_step(user_id, 'awaiting_log_channel')
        await event.edit("**📊 Set Log Channel**\n\nPlease send the Channel ID or Username for logs.", buttons=MenuBuilder.cancel_button())
        return

    if data == 'settings_replacements':
        await event.edit("**📝 Replacement Rules**", buttons=SettingsMenu.replacement_controls())
        return

    if data == 'add_rule':
        StateMachine.set_step(user_id, 'awaiting_rule_find')
        await event.edit(
            "**➕ Add Replacement Rule**\n\n"
            "Step 1: Send the text/link/username you want to **FIND**.",
            buttons=MenuBuilder.cancel_button()
        )
        return

    if data == 'list_rules':
        with get_db() as db:
            setting = db.query(GlobalSettings).filter(GlobalSettings.key == 'replacements').first()
            rules = json.loads(setting.value) if setting and setting.value else []

        if not rules:
            text = "No rules found."
        else:
            text = "**📋 Current Rules:**\n\n"
            for i, r in enumerate(rules):
                text += f"{i+1}. `{r['find']}` ➡️ `{r['replace']}`\n"

        await event.edit(text, buttons=SettingsMenu.replacement_controls())
        return

    # --- Toggles (Wizard Step 3) ---
    if data.startswith('toggle_'):
        state = StateMachine.get_state(user_id)
        if StateMachine.get_step(user_id) != 'config_mode':
            return

        current_config = state.get('config', {})
        key = data.replace('toggle_', '')

        # Flip boolean
        current_config[key] = not current_config.get(key, False)

        StateMachine.set_state(user_id, 'config', current_config)

        # Refresh Menu
        await event.edit(
            "**⚙️ Configure Rules**\n\n"
            "Select options for this task:",
            buttons=MenuBuilder.config_toggles(current_config)
        )
        return

    if data == 'save_task':
        await handle_save_task(event, user_id)
        return

    # --- Task List & Controls ---
    if data == 'list_tasks':
        with get_db() as db:
            tasks = db.query(Task).all()

        if not tasks:
            await event.edit("**📂 My Tasks**\n\nNo active tasks found.", buttons=MenuBuilder.back_button(b"cancel_action"))
            return

        # Simplified list view (Button for each task)
        buttons = []
        for t in tasks:
            buttons.append([Button.inline(f"{t.source_title} ➡️ {t.target_title}", f"view_task_{t.id}")])
        buttons.append([Button.inline("🔙 Back", b"cancel_action")])

        await event.edit("**📂 My Tasks**\n\nSelect a task to manage:", buttons=buttons)
        return

    if data.startswith('view_task_'):
        tid = int(data.split('_')[2])
        with get_db() as db:
            task = db.query(Task).filter(Task.id == tid).first()
            if not task:
                await event.answer("Task not found!", alert=True)
                return

            status = "🟢 Active" if task.is_active else "🔴 Paused"
            text = (
                f"**Task #{task.id}**\n"
                f"Source: {task.source_title}\n"
                f"Target: {task.target_title}\n"
                f"Status: {status}\n"
                f"Processed: {task.last_processed_id}"
            )
            await event.edit(text, buttons=MenuBuilder.task_controls(task.id))
        return

    # --- Task Actions (Pause/Delete) ---
    if data.startswith('pause_') or data.startswith('resume_'):
        tid = int(data.split('_')[1])
        with get_db() as db:
            task = db.query(Task).filter(Task.id == tid).first()
            if task:
                task.is_active = not task.is_active
                db.commit()
                # Refresh view
                status = "🟢 Active" if task.is_active else "🔴 Paused"
                text = (
                    f"**Task #{task.id}**\n"
                    f"Source: {task.source_title}\n"
                    f"Target: {task.target_title}\n"
                    f"Status: {status}\n"
                    f"Processed: {task.last_processed_id}"
                )
                await event.edit(text, buttons=MenuBuilder.task_controls(task.id))
        return

    if data.startswith('delete_'):
        tid = int(data.split('_')[1])
        with get_db() as db:
            db.query(Task).filter(Task.id == tid).delete()
            db.commit()
        await event.answer("Task deleted!", alert=True)
        # Return to list
        # Re-trigger list logic (copy-paste or recursive call - keeping it simple here)
        await event.edit("Task Deleted.", buttons=MenuBuilder.back_button(b"list_tasks"))
        return


@events.register(events.NewMessage(chats='me'))
async def wizard_input_handler(event):
    """Handles text input during the wizard flow."""
    user_id = event.sender_id
    step = StateMachine.get_step(user_id)

    if not step:
        return # Not in wizard

    # --- Step 1: Source ---
    if step == 'awaiting_source':
        try:
            entity = await event.client.get_entity(event.text)
            title = getattr(entity, 'title', entity.username)
            username = f"@{entity.username}" if entity.username else str(entity.id)

            StateMachine.set_state(user_id, 'source', username)
            StateMachine.set_state(user_id, 'source_title', title)
            StateMachine.set_step(user_id, 'awaiting_target')

            await event.respond(
                f"✅ Selected Source: **{title}**\n\n"
                "**Step 2/3:** Now send the **Target Channel**.",
                buttons=MenuBuilder.cancel_button()
            )
        except Exception as e:
            await event.respond(f"❌ Error finding channel: {e}\nPlease try again.", buttons=MenuBuilder.cancel_button())
        return

    # --- Settings: Log Channel ---
    if step == 'awaiting_log_channel':
        channel = event.text
        with get_db() as db:
            # Upsert
            setting = db.query(GlobalSettings).filter(GlobalSettings.key == 'log_channel').first()
            if not setting:
                setting = GlobalSettings(key='log_channel')
                db.add(setting)
            setting.value = json.dumps(channel)
            db.commit()

        StateMachine.clear_state(user_id)
        await event.respond(f"✅ Log Channel set to: `{channel}`", buttons=MenuBuilder.main_menu())
        return

    # --- Settings: Add Rule ---
    if step == 'awaiting_rule_find':
        StateMachine.set_state(user_id, 'rule_find', event.text)
        StateMachine.set_step(user_id, 'awaiting_rule_replace')
        await event.respond(
            f"FIND: `{event.text}`\n\n"
            "Step 2: Send the **REPLACEMENT** text.\n"
            "(Send `BLANK` to delete the text/link completely).",
            buttons=MenuBuilder.cancel_button()
        )
        return

    if step == 'awaiting_rule_replace':
        find = StateMachine.get_state(user_id).get('rule_find')
        replace = event.text
        if replace.strip().upper() == 'BLANK':
            replace = ''

        with get_db() as db:
            setting = db.query(GlobalSettings).filter(GlobalSettings.key == 'replacements').first()
            if not setting:
                setting = GlobalSettings(key='replacements', value=json.dumps([]))
                db.add(setting)

            current_rules = json.loads(setting.value) if setting.value else []
            current_rules.append({'find': find, 'replace': replace})
            setting.value = json.dumps(current_rules)
            db.commit()

        StateMachine.clear_state(user_id)
        await event.respond(
            f"✅ Rule Added:\n`{find}` ➡️ `{replace or '(Delete)'}`",
            buttons=SettingsMenu.replacement_controls()
        )
        return

    # --- Step 2: Target ---
    if step == 'awaiting_target':
        try:
            entity = await event.client.get_entity(event.text)
            title = getattr(entity, 'title', entity.username)
            username = f"@{entity.username}" if entity.username else str(entity.id)

            StateMachine.set_state(user_id, 'target', username)
            StateMachine.set_state(user_id, 'target_title', title)
            StateMachine.set_step(user_id, 'config_mode')

            # Default Config
            default_config = {'strip_links': False, 'strip_captions': False}
            StateMachine.set_state(user_id, 'config', default_config)

            await event.respond(
                f"✅ Selected Target: **{title}**\n\n"
                "**Step 3/3:** Configure Rules.",
                buttons=MenuBuilder.config_toggles(default_config)
            )
        except Exception as e:
            await event.respond(f"❌ Error finding channel: {e}\nPlease try again.", buttons=MenuBuilder.cancel_button())
        return
