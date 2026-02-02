import logging
import asyncio
from telethon import TelegramClient, events, errors
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel

from app.database.session import AsyncSessionLocal
from app.database.crud import get_all_tasks
from app.core.replacements import perform_replacements

logger = logging.getLogger(__name__)

class UserbotClient:
    def __init__(self, session_string, api_id, api_hash):
        # Determine if session_string is a file path or a StringSession
        # A typical StringSession starts with alphanumeric characters and is long.
        # A file path usually has extension or path separators.
        # However, for this simplified logic, we'll try to use StringSession if it looks like one.

        session = session_string
        if session_string and len(session_string) > 50 and '/' not in session_string and '\\' not in session_string:
             session = StringSession(session_string)

        self.client = TelegramClient(
            session,
            api_id,
            api_hash
        )
        self.session_string = session_string

    async def start(self):
        logger.info("Starting Userbot Client...")
        await self.client.start()

        # Register handlers
        self.client.add_event_handler(self.message_handler, events.NewMessage(incoming=True))

        me = await self.client.get_me()
        logger.info(f"Userbot connected as: {me.username} ({me.id})")

    async def join_channel(self, channel_username):
        """
        Attempts to join a public channel.
        """
        try:
            logger.info(f"Attempting to join {channel_username}...")
            entity = await self.client.get_entity(channel_username)

            # Check if left, though get_entity usually implies visibility
            if isinstance(entity, Channel) and entity.left:
                 pass # proceed to join

            await self.client(JoinChannelRequest(entity))
            logger.info(f"Successfully joined {channel_username}")
            return True
        except errors.UserAlreadyParticipantError:
            logger.info(f"Already a participant of {channel_username}")
            return True
        except Exception as e:
            logger.error(f"Failed to join {channel_username}: {e}")
            return False

    async def message_handler(self, event):
        if event.is_private:
            return

        # Load tasks from DB
        # OPTIMIZATION: In production, we should cache this and update on changes
        async with AsyncSessionLocal() as session:
            tasks = await get_all_tasks(session)

        if not tasks:
            return

        try:
            chat = await event.get_chat()
            if not hasattr(chat, 'username') or not chat.username:
                return

            chat_username = f"@{chat.username}"

            for task in tasks:
                # Basic matching by username string for now
                # TODO: Implement ID-based matching in future steps
                if task.source and task.source.lower() == chat_username.lower():
                    try:
                        original_text = event.text or ""

                        # Convert task object to dict for replacement function
                        task_dict = {
                            'find_user': task.find_user,
                            'replace_user': task.replace_user,
                            'find_link': task.find_link,
                            'replace_link': task.replace_link
                        }

                        modified_text = perform_replacements(original_text, task_dict)

                        if task.target:
                            await self.client.send_message(task.target, modified_text, file=event.message.media)
                            logger.info(f"Forwarded message from {task.source} to {task.target}")
                    except Exception as e:
                        logger.error(f"Error processing message from {task.source}: {e}")

        except Exception as e:
            logger.debug(f"Error in monitor loop: {e}")

    async def stop(self):
        await self.client.disconnect()
