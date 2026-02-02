import asyncio
import logging
import os
from dotenv import load_dotenv

from app.database.session import init_db
from app.core.userbot import UserbotClient
from app.core.bot import BotClient
from app.core.brain import JulesBrain

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    # 1. Initialize Database
    logger.info("Initializing Database...")
    await init_db()

    # 2. Load Config
    API_ID = int(os.getenv('API_ID', 0))
    API_HASH = os.getenv('API_HASH')
    SESSION_STRING = os.getenv('SESSION_STRING')
    BOT_TOKEN = os.getenv('BOT_TOKEN') # For the UI bot

    if not all([API_ID, API_HASH, SESSION_STRING]):
        logger.critical("Missing API_ID, API_HASH, or SESSION_STRING")
        return

    # 3. Start Userbot
    userbot = UserbotClient(SESSION_STRING, API_ID, API_HASH)
    await userbot.start()

    # 4. Start Bot (if token provided)
    bot = None
    if BOT_TOKEN:
        bot = BotClient(BOT_TOKEN, API_ID, API_HASH)

        # Inject Brain into Bot (Simplified injection for now)
        brain = JulesBrain()

        # Override Bot's command handler to use Brain
        # This is a quick integration; in a fuller app we'd pass brain in init
        original_handler = bot.command_handler
        async def brain_handler(event):
            response = await brain.process_text(event.raw_text)
            await event.reply(response)

        bot.command_handler = brain_handler
        # Re-register with new handler logic in a real pattern,
        # but for Telethon generic handler:
        from telethon import events
        bot.client.add_event_handler(brain_handler, events.NewMessage(incoming=True))

        await bot.start()
    else:
        logger.warning("BOT_TOKEN not provided. UI Bot will not run.")

    logger.info("Jules System is Running...")

    # Keep running
    try:
        await userbot.client.run_until_disconnected()
    finally:
        await userbot.stop()
        if bot:
            await bot.stop()

if __name__ == '__main__':
    asyncio.run(main())
