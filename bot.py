import os
import logging
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from config_state import init_config
from handlers.command_handler import command_handler
from handlers.message_monitor import message_monitor

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_STRING = os.getenv('SESSION_STRING')

# Validation
if not all([API_ID, API_HASH, SESSION_STRING]):
    logger.critical("Missing API_ID, API_HASH, or SESSION_STRING environment variables.")

try:
    client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)
except Exception as e:
    logger.error(f"Failed to initialize client: {e}")
    client = None

# Register Event Handlers
if client:
    @client.on(events.NewMessage(chats='me'))
    async def on_command_handler(event):
        await command_handler(event, client)

    @client.on(events.NewMessage(incoming=True))
    async def on_message_monitor(event):
        await message_monitor(event, client)

async def main():
    logger.info("Starting Userbot...")
    await client.start()
    
    # Initialize cache
    await init_config(client)
    
    me = await client.get_me()
    logger.info(f"Logged in as: {me.username} ({me.id})")
    
    # Keep running
    await client.run_until_disconnected()

if __name__ == '__main__':
    if client:
        client.loop.run_until_complete(main())
