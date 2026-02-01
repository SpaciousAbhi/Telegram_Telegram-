import os
import logging
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

# App Imports
from app.database.db import initialize_database
from app.plugins import commands, callbacks
from app.core.engine import live_monitor
from app.core.history import history_worker

# Load Env
load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_STRING = os.getenv('SESSION_STRING')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Validation
if not all([API_ID, API_HASH, SESSION_STRING, BOT_TOKEN]):
    logger.critical("❌ Missing Env Vars! Please ensure API_ID, API_HASH, SESSION_STRING, and BOT_TOKEN are set.")
    exit(1)

async def main():
    # 1. Database Init
    initialize_database()
    logger.info("Database Initialized.")

    # 2. Clients Init
    try:
        # Userbot (The Worker)
        user_client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)
        await user_client.start()
        logger.info(f"Userbot started as: {(await user_client.get_me()).username}")

        # Bot (The Controller)
        bot_client = TelegramClient('bot_session', int(API_ID), API_HASH)
        await bot_client.start(bot_token=BOT_TOKEN)
        logger.info(f"Controller Bot started as: {(await bot_client.get_me()).username}")

    except Exception as e:
        logger.critical(f"Failed to start clients: {e}")
        return

    # 3. Register Event Handlers

    # --- Controller Bot Handlers (UI) ---
    bot_client.add_event_handler(commands.start_handler)
    bot_client.add_event_handler(callbacks.callback_handler)
    bot_client.add_event_handler(callbacks.wizard_input_handler)

    # --- Userbot Handlers (Worker) ---
    user_client.add_event_handler(live_monitor)

    logger.info("Event Handlers Registered.")

    # 4. Start Background Workers
    asyncio.create_task(history_worker(user_client))
    logger.info("History Worker Started.")

    # 5. Run Both
    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected()
    )

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
