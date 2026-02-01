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

async def main():
    # 1. Database Init
    initialize_database()
    logger.info("Database Initialized.")

    # 2. Client Init
    try:
        client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)
        await client.start()
        logger.info(f"Bot started as: {(await client.get_me()).username}")
    except Exception as e:
        logger.critical(f"Failed to start client: {e}")
        return

    # 3. Load Plugins (Event Handlers)
    # Commands
    client.add_event_handler(commands.start_handler)
    # Callbacks (Buttons)
    client.add_event_handler(callbacks.callback_handler)
    # Wizard Input
    client.add_event_handler(callbacks.wizard_input_handler)
    # Live Monitor
    client.add_event_handler(live_monitor)

    logger.info("Event Handlers Registered.")

    # 4. Start Background Workers
    asyncio.create_task(history_worker(client))
    logger.info("History Worker Started.")

    # 5. Run
    await client.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
