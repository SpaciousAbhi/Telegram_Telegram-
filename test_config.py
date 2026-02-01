import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from config_manager import load_config, save_config, CONFIG_HEADER
import json

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        
    def test_load_config_found(self):
        # Mock message
        mock_msg = MagicMock()
        config_data = {"tasks": [{"id": 1}]}
        mock_msg.text = f"{CONFIG_HEADER}\n" + json.dumps(config_data)
        
        # Mock iter_messages to yield the message
        async def async_iter(*args, **kwargs):
            yield mock_msg
            
        self.client.iter_messages = MagicMock(side_effect=async_iter)
        
        result = asyncio.run(load_config(self.client))
        self.assertEqual(result, config_data)

    def test_load_config_not_found(self):
        # Mock iter_messages to yield nothing
        async def async_iter(*args, **kwargs):
            if False: yield None
            
        self.client.iter_messages = MagicMock(side_effect=async_iter)
        
        result = asyncio.run(load_config(self.client))
        self.assertEqual(result, {"tasks": []})

    def test_save_config_update(self):
        # Mock existing message
        mock_msg = AsyncMock()
        
        async def async_iter(*args, **kwargs):
            yield mock_msg
            
        self.client.iter_messages = MagicMock(side_effect=async_iter)
        
        new_config = {"tasks": [{"id": 2}]}
        asyncio.run(save_config(self.client, new_config))
        
        # Check if edit was called
        expected_text = f"{CONFIG_HEADER}\n" + json.dumps(new_config, indent=2)
        mock_msg.edit.assert_called_once_with(expected_text)

    def test_save_config_new(self):
        # Mock no existing message
        async def async_iter(*args, **kwargs):
            if False: yield None
            
        self.client.iter_messages = MagicMock(side_effect=async_iter)
        self.client.send_message = AsyncMock()
        
        new_config = {"tasks": [{"id": 3}]}
        asyncio.run(save_config(self.client, new_config))
        
        # Check if send_message was called
        expected_text = f"{CONFIG_HEADER}\n" + json.dumps(new_config, indent=2)
        self.client.send_message.assert_called_once_with('me', expected_text)

if __name__ == '__main__':
    unittest.main()
