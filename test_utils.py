import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from utils import join_channel
from telethon import errors
from telethon.tl.types import Channel

class TestUtils(unittest.TestCase):
    def setUp(self):
        self.client = AsyncMock()
        # Ensure get_entity is also an AsyncMock (it is by default with AsyncMock parent)
        # Ensure calling client() is awaitable (it is by default with AsyncMock)

    def test_join_channel_success(self):
        self.client.get_entity.return_value = MagicMock()

        result = asyncio.run(join_channel(self.client, '@channel'))

        self.assertTrue(result)
        self.client.get_entity.assert_called_once_with('@channel')
        self.client.assert_called_once() # JoinChannelRequest

    def test_join_channel_already_participant(self):
        # When calling client(), raise error.
        # Since client is AsyncMock, client() returns a coroutine.
        # side_effect on an AsyncMock triggers when awaited.
        self.client.side_effect = errors.UserAlreadyParticipantError(request=None)

        result = asyncio.run(join_channel(self.client, '@channel'))

        self.assertTrue(result)

    def test_join_channel_failure(self):
        self.client.side_effect = Exception("Generic Error")

        result = asyncio.run(join_channel(self.client, '@channel'))

        self.assertFalse(result)

    def test_join_channel_left(self):
        mock_entity = MagicMock(spec=Channel)
        mock_entity.left = True
        self.client.get_entity.return_value = mock_entity

        result = asyncio.run(join_channel(self.client, '@channel'))

        self.assertTrue(result)
        self.client.assert_called_once()

if __name__ == '__main__':
    unittest.main()
