import logging
from config_manager import load_config, save_config

logger = logging.getLogger(__name__)

# Global cache
_CACHED_CONFIG = None

async def init_config(client):
    """Initializes the configuration cache."""
    global _CACHED_CONFIG
    _CACHED_CONFIG = await load_config(client)
    return _CACHED_CONFIG

def get_cached_config():
    """Returns the cached configuration. Assumes init_config has been called."""
    return _CACHED_CONFIG or {"tasks": []}

async def update_config(client, new_config):
    """Updates the cache and persists the configuration."""
    global _CACHED_CONFIG
    _CACHED_CONFIG = new_config
    await save_config(client, new_config)
