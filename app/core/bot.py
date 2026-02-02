import logging
import os
from telethon import TelegramClient, events

# We'll use the same library (Telethon) for the Bot API client for consistency,
# although aiogram is also popular. Telethon handles Bot API tokens just fine.

logger = logging.getLogger(__name__)

class BotClient:
    def __init__(self, bot_token, api_id, api_hash):
        self.client = TelegramClient(
            'bot_session', # Session name for local file
            api_id,
            api_hash
        )
        self.bot_token = bot_token

    async def start(self):
        logger.info("Starting Bot Client...")
        await self.client.start(bot_token=self.bot_token)

        # Register handlers
        self.client.add_event_handler(self.command_handler, events.NewMessage(pattern='/start'))

        me = await self.client.get_me()
        logger.info(f"Bot connected as: {me.username} ({me.id})")

    async def command_handler(self, event):
        await event.reply("Hello! I am Jules, your forwarding assistant.\n"
                          "Use my AI capabilities or commands to configure tasks.")

    async def stop(self):
        await self.client.disconnect()
