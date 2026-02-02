import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Mock telethon
sys.modules['telethon'] = MagicMock()
sys.modules['telethon.sync'] = MagicMock()
sys.modules['telethon.sessions'] = MagicMock()
sys.modules['telethon.tl.functions.channels'] = MagicMock()
sys.modules['telethon.tl.types'] = MagicMock()

# Mock config_state - we can mock this one as it's stateful/external dependency heavy
sys.modules['config_state'] = MagicMock()

# We do NOT mock 'utils' globally here because it breaks test_replacements.py
# which expects the real utils module.
# Instead, we will patch the specific imports in handlers.command_handler

from handlers.command_handler import command_handler

class TestCommandHandler(unittest.IsolatedAsyncioTestCase):
    async def test_help_command(self):
        event = AsyncMock()
        event.raw_text = '/help'
        client = AsyncMock()

        await command_handler(event, client)

        event.reply.assert_called_once()
        args, _ = event.reply.call_args
        self.assertIn("**🤖 Userbot Commands**", args[0])

    async def test_list_command_empty(self):
        event = AsyncMock()
        event.raw_text = '/list'
        client = AsyncMock()

        # Mock get_cached_config
        with patch('handlers.command_handler.get_cached_config', new_callable=AsyncMock) as mock_get_config:
            mock_get_config.return_value = {'tasks': []}

            await command_handler(event, client)

            event.reply.assert_called_with("No active tasks found.")

    async def test_add_command_success(self):
        event = AsyncMock()
        event.raw_text = "/add\nsource: @src\ntarget: @tgt"
        client = AsyncMock()

        # We need to patch join_channel where it is imported in handlers.command_handler
        with patch('handlers.command_handler.get_cached_config', new_callable=AsyncMock) as mock_get_config, \
             patch('handlers.command_handler.update_cached_config', new_callable=AsyncMock) as mock_update_config, \
             patch('handlers.command_handler.join_channel', new_callable=AsyncMock) as mock_join:

            mock_get_config.return_value = {'tasks': []}
            mock_join.return_value = True

            await command_handler(event, client)

            # Verify update_cached_config called with new task
            mock_update_config.assert_called_once()
            updated_config = mock_update_config.call_args[0][1]
            self.assertEqual(len(updated_config['tasks']), 1)
            self.assertEqual(updated_config['tasks'][0]['source'], '@src')
            self.assertEqual(updated_config['tasks'][0]['target'], '@tgt')

            event.reply.assert_called()
            self.assertIn("Task added!", event.reply.call_args[0][0])

if __name__ == '__main__':
    unittest.main()
