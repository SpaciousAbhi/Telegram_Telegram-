from config_manager import load_config, save_config

# Global Config Cache
CACHED_CONFIG = None

async def get_cached_config(client):
    global CACHED_CONFIG
    if CACHED_CONFIG is None:
        CACHED_CONFIG = await load_config(client)
    return CACHED_CONFIG

async def update_cached_config(client, new_config):
    global CACHED_CONFIG
    CACHED_CONFIG = new_config
    await save_config(client, new_config)
