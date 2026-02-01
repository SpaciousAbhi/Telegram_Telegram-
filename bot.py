import os
import logging
import asyncio
import re
from dotenv import load_dotenv
from telethon import TelegramClient, events, errors
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel

from config_manager import load_config, save_config

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
    # We don't exit here strictly to allow unit testing import, but runtime will fail.

try:
    client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)
except Exception as e:
    logger.error(f"Failed to initialize client: {e}")
    client = None

# Global Config Cache
CACHED_CONFIG = None

async def get_cached_config():
    global CACHED_CONFIG
    if CACHED_CONFIG is None:
        CACHED_CONFIG = await load_config(client)
    return CACHED_CONFIG

async def update_cached_config(new_config):
    global CACHED_CONFIG
    CACHED_CONFIG = new_config
    await save_config(client, new_config)

async def join_channel(channel_username):
    """
    Attempts to join a public channel.
    Returns True if successful or already a member, False otherwise.
    """
    try:
        logger.info(f"Attempting to join {channel_username}...")
        entity = await client.get_entity(channel_username)
        
        if isinstance(entity, Channel) and entity.left:
             pass
        
        await client(JoinChannelRequest(entity))
        logger.info(f"Successfully joined {channel_username}")
        return True
    except errors.UserAlreadyParticipantError:
        logger.info(f"Already a participant of {channel_username}")
        return True
    except Exception as e:
        logger.error(f"Failed to join {channel_username}: {e}")
        return False

def perform_replacements(text, task):
    """
    Performs safe regex replacements on the text based on task config.
    """
    if not text:
        return text
        
    # User Replacement
    find_user = task.get('find_user')
    replace_user = task.get('replace_user')
    
    if find_user and replace_user:
        escaped_find = re.escape(find_user)
        # Pattern: (?<!\w)@username\b
        pattern = r'(?<!\w)' + escaped_find + r'\b'
        text = re.sub(pattern, replace_user, text, flags=re.IGNORECASE)

    # Link Replacement
    find_link = task.get('find_link')
    replace_link = task.get('replace_link')
    
    if find_link and replace_link:
        escaped_link = re.escape(find_link)
        # Pattern: (?<!\w)link(?!\w)
        pattern = r'(?<!\w)' + escaped_link + r'(?!\w)'
        text = re.sub(pattern, replace_link, text, flags=re.IGNORECASE)
        
    return text

# --- Command Handler ---

@client.on(events.NewMessage(chats='me'))
async def command_handler(event):
    """
    Handles commands sent to 'Saved Messages'.
    """
    text = event.raw_text
    
    if text.startswith('/help'):
        help_text = (
            "**🤖 Userbot Commands**\n\n"
            "`/list` - List all active tasks\n"
            "`/del <ID>` - Delete a task by ID\n"
            "`/add` - Add a new task (see template below)\n\n"
            "**Add Task Template:**\n"
            "```\n"
            "/add\n"
            "source: @SourceChannel\n"
            "target: @TargetChannel\n"
            "find_user: @OldUser (optional)\n"
            "replace_user: @NewUser (optional)\n"
            "find_link: t.me/OldLink (optional)\n"
            "replace_link: t.me/NewLink (optional)\n"
            "```"
        )
        await event.reply(help_text)
        return

    if text.startswith('/list'):
        config = await get_cached_config()
        tasks = config.get('tasks', [])
        
        if not tasks:
            await event.reply("No active tasks found.")
            return
            
        msg = "**📋 Active Tasks:**\n\n"
        for i, task in enumerate(tasks):
            msg += (
                f"**ID: {i}**\n"
                f"Source: `{task.get('source')}`\n"
                f"Target: `{task.get('target')}`\n"
                f"Find/Rep User: `{task.get('find_user', 'N/A')}` -> `{task.get('replace_user', 'N/A')}`\n"
                f"Find/Rep Link: `{task.get('find_link', 'N/A')}` -> `{task.get('replace_link', 'N/A')}`\n"
                "-------------------\n"
            )
        await event.reply(msg)
        return

    if text.startswith('/del'):
        try:
            _, task_id = text.split(maxsplit=1)
            task_id = int(task_id)
            
            config = await get_cached_config()
            tasks = config.get('tasks', [])
            
            if 0 <= task_id < len(tasks):
                removed = tasks.pop(task_id)
                await update_cached_config(config)
                await event.reply(f"✅ Deleted task for source: `{removed.get('source')}`")
            else:
                await event.reply("❌ Invalid Task ID.")
                
        except ValueError:
            await event.reply("❌ Usage: `/del <ID>`")
        return

    if text.startswith('/add'):
        lines = text.splitlines()
        task = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key in ['source', 'target', 'find_user', 'replace_user', 'find_link', 'replace_link']:
                    task[key] = value
        
        # Validation
        if 'source' not in task or 'target' not in task:
            await event.reply("❌ Error: `source` and `target` are required.")
            return
            
        # Try to join source
        joined = await join_channel(task['source'])
        if not joined:
            await event.reply(f"⚠️ Warning: Could not join `{task['source']}`. Monitoring might not work if you are not a member.")
        
        # Save
        config = await get_cached_config()
        if 'tasks' not in config:
            config['tasks'] = []
            
        config['tasks'].append(task)
        await update_cached_config(config)
        
        await event.reply(f"✅ Task added!\nMonitoring: `{task['source']}` -> `{task['target']}`")
        return

# --- Message Monitor ---

@client.on(events.NewMessage(incoming=True))
async def message_monitor(event):
    """
    Monitors incoming messages from source channels.
    """
    if event.is_private:
        return

    # Check if we have cached config
    config = await get_cached_config()
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
                        await client.send_message(target, modified_text, file=event.message.media)
                        logger.info(f"Forwarded message from {source} to {target}")
                except Exception as e:
                    logger.error(f"Error processing message from {source}: {e}")
                    
    except Exception as e:
        logger.debug(f"Error in monitor loop: {e}")

async def main():
    logger.info("Starting Userbot...")
    await client.start()
    
    # Initialize cache
    await get_cached_config()
    
    me = await client.get_me()
    logger.info(f"Logged in as: {me.username} ({me.id})")
    
    # Keep running
    await client.run_until_disconnected()

if __name__ == '__main__':
    if client:
        client.loop.run_until_complete(main())
