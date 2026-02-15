from config_manager import load_config, save_config

class ConfigState:
    _cached_config = None

    @classmethod
    async def get(cls, client):
        if cls._cached_config is None:
            cls._cached_config = await load_config(client)
        return cls._cached_config

    @classmethod
    async def update(cls, client, new_config):
        cls._cached_config = new_config
        await save_config(client, new_config)
