import logging
from telethon import events
from config_state import ConfigState
from utils import perform_replacements

logger = logging.getLogger(__name__)

def register_message_monitor(client):
    @client.on(events.NewMessage(incoming=True))
    async def message_monitor(event):
        """
        Monitors incoming messages from source channels.
        """
        if event.is_private:
            return

        # Check if we have cached config
        config = await ConfigState.get(client)
        tasks = config.get('tasks', [])

        if not tasks:
            return

        try:
            chat = await event.get_chat()
            if not hasattr(chat, 'username') or not chat.username:
                return

            chat_username = f"@{chat.username}"

            # Filter tasks for this source
            matching_tasks = [t for t in tasks if t.get('source', '').lower() == chat_username.lower()]

            if not matching_tasks:
                return

            # Group by target
            tasks_by_target = {}
            for task in matching_tasks:
                target = task.get('target')
                if not target: continue

                target_key = target.lower()
                if target_key not in tasks_by_target:
                    tasks_by_target[target_key] = {'target': target, 'tasks': []}
                tasks_by_target[target_key]['tasks'].append(task)

            # Process each target
            for target_key, data in tasks_by_target.items():
                target = data['target']
                target_tasks = data['tasks']

                try:
                    original_text = event.text or ""
                    modified_text = original_text

                    for task in target_tasks:
                        modified_text = perform_replacements(modified_text, task)

                    await client.send_message(target, modified_text, file=event.message.media)
                    logger.info(f"Forwarded message from {chat_username} to {target} with {len(target_tasks)} replacements applied")

                except Exception as e:
                    logger.error(f"Error processing message from {chat_username} to {target}: {e}")

        except Exception as e:
            logger.debug(f"Error in monitor loop: {e}")
