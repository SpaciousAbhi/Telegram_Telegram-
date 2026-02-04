import os
import logging
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Import handlers
from handlers.command_handler import command_handler
from handlers.message_monitor import message_monitor
import config_state

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

async def main():
    logger.info("Starting Userbot...")
    await client.start()
    
    # Initialize cache
    await config_state.get_cached_config(client)

    # Register Handlers
    client.add_event_handler(command_handler, events.NewMessage(chats='me'))
    client.add_event_handler(message_monitor, events.NewMessage(incoming=True))
    
    me = await client.get_me()
    logger.info(f"Logged in as: {me.username} ({me.id})")
    
    # Keep running
    await client.run_until_disconnected()

if __name__ == '__main__':
    if client:
        client.loop.run_until_complete(main())
