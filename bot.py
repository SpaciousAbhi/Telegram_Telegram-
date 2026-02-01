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
TASK_INDEX = {}  # Map: source_username.lower() -> [list of tasks]

def rebuild_task_index(tasks):
    """
    Rebuilds the global TASK_INDEX for O(1) lookup.
    """
    global TASK_INDEX
    TASK_INDEX = {}
    for task in tasks:
        source = task.get('source')
        if source:
            source = source.lower()
            if source not in TASK_INDEX:
                TASK_INDEX[source] = []
            TASK_INDEX[source].append(task)

async def get_cached_config():
    global CACHED_CONFIG
    if CACHED_CONFIG is None:
        CACHED_CONFIG = await load_config(client)
        rebuild_task_index(CACHED_CONFIG.get('tasks', []))
    return CACHED_CONFIG

async def update_cached_config(new_config):
    global CACHED_CONFIG
    CACHED_CONFIG = new_config
    rebuild_task_index(new_config.get('tasks', []))
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

    # Helper function for applying a single replacement
    def apply_single(txt, r_type, find, replace):
        if not find or not replace:
            return txt
        
        if r_type == 'user':
            escaped_find = re.escape(find)
            # Pattern: (?<!\w)@username\b
            pattern = r'(?<!\w)' + escaped_find + r'\b'
            return re.sub(pattern, replace, txt, flags=re.IGNORECASE)

        elif r_type == 'link':
            escaped_link = re.escape(find)
            # Pattern: (?<!\w)link(?!\w)
            pattern = r'(?<!\w)' + escaped_link + r'(?!\w)'
            return re.sub(pattern, replace, txt, flags=re.IGNORECASE)
        return txt

    # 1. Process new 'replacements' list
    replacements = task.get('replacements', [])
    for rep in replacements:
        text = apply_single(text, rep.get('type'), rep.get('find'), rep.get('replace'))

    # 2. Process legacy User Replacement
    find_user = task.get('find_user')
    replace_user = task.get('replace_user')
    if find_user and replace_user:
        text = apply_single(text, 'user', find_user, replace_user)

    # 3. Process legacy Link Replacement
    find_link = task.get('find_link')
    replace_link = task.get('replace_link')
    if find_link and replace_link:
        text = apply_single(text, 'link', find_link, replace_link)
        
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
            "replace_user: @OldUser -> @NewUser\n"
            "replace_link: old.link -> new.link\n"
            "```\n"
            "You can add multiple `replace_user` and `replace_link` lines."
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
            )

            # Show Replacements
            replacements = task.get('replacements', [])
            for rep in replacements:
                msg += f"Rep ({rep.get('type')}): `{rep.get('find')}` -> `{rep.get('replace')}`\n"

            # Legacy
            if task.get('find_user'):
                msg += f"Rep (user): `{task.get('find_user')}` -> `{task.get('replace_user')}`\n"
            if task.get('find_link'):
                msg += f"Rep (link): `{task.get('find_link')}` -> `{task.get('replace_link')}`\n"

            msg += "-------------------\n"
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
        task = {'replacements': []}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key in ['source', 'target']:
                    task[key] = value

                elif key == 'replace_user' or key == 'replace_link':
                    if '->' in value:
                        find, replace = value.split('->', 1)
                        find = find.strip()
                        replace = replace.strip()

                        r_type = 'user' if key == 'replace_user' else 'link'
                        task['replacements'].append({
                            'type': r_type,
                            'find': find,
                            'replace': replace
                        })
                    else:
                        # Fallback for legacy parsing if mixed or just using old style
                        if key == 'replace_user':
                             task['replace_user'] = value
                        elif key == 'replace_link':
                             task['replace_link'] = value

                elif key == 'find_user':
                     task['find_user'] = value
                elif key == 'find_link':
                     task['find_link'] = value
        
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
        
        # Look up tasks using index
        relevant_tasks = TASK_INDEX.get(chat_username.lower(), [])

        for task in relevant_tasks:
            try:
                original_text = event.text or ""
                modified_text = perform_replacements(original_text, task)

                target = task.get('target')
                if target:
                    await client.send_message(target, modified_text, file=event.message.media)
                    logger.info(f"Forwarded message from {chat_username} to {target}")
            except Exception as e:
                logger.error(f"Error processing message from {chat_username}: {e}")
                    
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
