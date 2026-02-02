import json
import logging

# Unique header to identify the configuration message in Saved Messages
CONFIG_HEADER = "#USERBOT_CONFIG_V1"

# Global Config Cache
CACHED_CONFIG = None

async def get_cached_config(client):
    """
    Returns the cached configuration, loading it if necessary.
    """
    global CACHED_CONFIG
    if CACHED_CONFIG is None:
        CACHED_CONFIG = await load_config(client)
    return CACHED_CONFIG

async def update_cached_config(client, new_config):
    """
    Updates the cached configuration and saves it to Telegram.
    """
    global CACHED_CONFIG
    CACHED_CONFIG = new_config
    await save_config(client, new_config)

async def load_config(client):
    """
    Searches for the configuration message in 'Saved Messages' (me).
    Returns the parsed configuration dictionary or an empty default structure.
    """
    try:
        # Search for the message containing the header in 'me' chat
        # We search specifically for the header to avoid iterating everything
        async for message in client.iter_messages('me', search=CONFIG_HEADER, limit=1):
            try:
                # The message content should be: HEADER\nJSON_STRING
                content = message.text
                if not content.startswith(CONFIG_HEADER):
                    continue
                
                json_str = content.replace(CONFIG_HEADER, "", 1).strip()
                if not json_str:
                    return {"tasks": []}
                
                return json.loads(json_str)
            except json.JSONDecodeError:
                logging.error("Found config message but failed to decode JSON.")
                continue
        
        # If no message found
        return {"tasks": []}
        
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {"tasks": []}

async def save_config(client, config):
    """
    Saves the configuration dictionary to 'Saved Messages'.
    Updates the existing message if found, otherwise creates a new one.
    """
    try:
        json_str = json.dumps(config, indent=2)
        new_text = f"{CONFIG_HEADER}\n{json_str}"
        
        # Search for existing message to update
        existing_msg = None
        async for message in client.iter_messages('me', search=CONFIG_HEADER, limit=1):
             existing_msg = message
             break
        
        if existing_msg:
            await existing_msg.edit(new_text)
        else:
            sent_msg = await client.send_message('me', new_text)
            try:
                await sent_msg.pin()
            except Exception:
                pass # Pinning might fail if too many pins, but it's not critical
                
    except Exception as e:
        logging.error(f"Error saving config: {e}")
        raise e
