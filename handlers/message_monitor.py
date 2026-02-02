import logging
from telethon import events
from config_state import get_cached_config
from utils import perform_replacements

logger = logging.getLogger(__name__)

async def message_monitor_func(event, client):
    """
    Monitors incoming messages from source channels.
    """
    if event.is_private:
        return

    # Check if we have cached config
    config = get_cached_config()
    tasks = config.get('tasks', [])

    if not tasks:
        return

    try:
        chat = await event.get_chat()
        if not hasattr(chat, 'username') or not chat.username:
            return

        chat_username = f"@{chat.username}"

        for task in tasks:
            source = task.get('source')
            if source and source.lower() == chat_username.lower():
                try:
                    original_text = event.text or ""
                    modified_text = perform_replacements(original_text, task)

                    target = task.get('target')
                    if target:
                        try:
                            await client.send_message(target, modified_text, file=event.message.media)
                            logger.info(f"Forwarded message from {source} to {target}")
                        except Exception as send_err:
                            logger.error(f"Failed to send message to {target}: {send_err}")
                except Exception as e:
                    logger.error(f"Error processing message from {source}: {e}")

    except Exception as e:
        logger.debug(f"Error in monitor loop: {e}")

def register_message_monitor(client):
    @client.on(events.NewMessage(incoming=True))
    async def wrapper(event):
        await message_monitor_func(event, client)
