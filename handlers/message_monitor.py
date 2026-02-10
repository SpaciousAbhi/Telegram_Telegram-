import logging
import asyncio
from telethon import events
from config_manager import get_cached_config
from utils import perform_replacements

logger = logging.getLogger(__name__)

def register_message_monitor(client):
    """
    Registers the message monitor for incoming messages.
    """

    @client.on(events.NewMessage(incoming=True))
    async def message_monitor(event):
        """
        Monitors incoming messages from source channels.
        """
        if event.is_private:
            return

        # Check if we have cached config
        config = await get_cached_config(client)
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
                            # Retry logic for sending message
                            max_retries = 3
                            for attempt in range(max_retries):
                                try:
                                    await client.send_message(target, modified_text, file=event.message.media)
                                    logger.info(f"Forwarded message from {source} to {target}")
                                    break
                                except Exception as send_err:
                                    if attempt < max_retries - 1:
                                        wait_time = (attempt + 1) * 2
                                        logger.warning(f"Failed to send to {target} (Attempt {attempt+1}/{max_retries}). Retrying in {wait_time}s... Error: {send_err}")
                                        await asyncio.sleep(wait_time)
                                    else:
                                        logger.error(f"Failed to send to {target} after {max_retries} attempts: {send_err}")
                                        raise send_err

                    except Exception as e:
                        logger.error(f"Error processing message from {source}: {e}")

        except Exception as e:
            logger.debug(f"Error in monitor loop: {e}")
