from config_manager import load_config, save_config

# Global Config Cache
_CACHED_CONFIG = None

async def get_cached_config(client):
    global _CACHED_CONFIG
    if _CACHED_CONFIG is None:
        _CACHED_CONFIG = await load_config(client)
    return _CACHED_CONFIG

async def update_cached_config(client, new_config):
    global _CACHED_CONFIG
    _CACHED_CONFIG = new_config
    await save_config(client, new_config)
