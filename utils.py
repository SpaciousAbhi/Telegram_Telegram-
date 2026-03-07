import re
import logging
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel
from telethon import errors

logger = logging.getLogger(__name__)

async def join_channel(client, channel_username):
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
