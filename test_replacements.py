import unittest
import sys
from unittest.mock import MagicMock
import re

# Mock telethon
sys.modules['telethon'] = MagicMock()
sys.modules['telethon.sync'] = MagicMock()
sys.modules['telethon.sessions'] = MagicMock()
sys.modules['telethon.tl.functions.channels'] = MagicMock()
sys.modules['telethon.tl.types'] = MagicMock()

# Mock TelegramClient
mock_client = MagicMock()
mock_client.on = MagicMock(return_value=lambda x: x)
sys.modules['telethon'].TelegramClient.return_value = mock_client

import os
os.environ['API_ID'] = '12345'
os.environ['API_HASH'] = 'fakehash'
os.environ['SESSION_STRING'] = 'fakesession'

from bot import perform_replacements

class TestReplacements(unittest.TestCase):
    def test_legacy_replacement(self):
        task = {
            'find_user': '@old',
            'replace_user': '@new',
            'find_link': 't.me/old',
            'replace_link': 't.me/new'
        }
        
        text = "Hello @old check t.me/old"
        expected = "Hello @new check t.me/new"
        self.assertEqual(perform_replacements(text, task), expected)

    def test_new_replacements_list(self):
        task = {
            'replacements': [
                {'type': 'user', 'find': '@u1', 'replace': '@u2'},
                {'type': 'link', 'find': 'link1', 'replace': 'link2'}
            ]
        }
        text = "Hi @u1 go to link1"
        expected = "Hi @u2 go to link2"
        self.assertEqual(perform_replacements(text, task), expected)

    def test_multiple_replacements(self):
        task = {
            'replacements': [
                {'type': 'user', 'find': '@a', 'replace': '@b'},
                {'type': 'user', 'find': '@b', 'replace': '@c'}, # Sequential?
                {'type': 'user', 'find': '@x', 'replace': '@y'}
            ]
        }
        text = "Hello @a and @x"
        # If sequential: @a -> @b, then later @b -> @c. So @a becomes @c.
        expected = "Hello @c and @y"
        self.assertEqual(perform_replacements(text, task), expected)

    def test_mixed_legacy_and_new(self):
        task = {
            'replacements': [
                {'type': 'user', 'find': '@list', 'replace': '@list_replaced'}
            ],
            'find_user': '@legacy',
            'replace_user': '@legacy_replaced'
        }
        text = "See @list and @legacy"
        expected = "See @list_replaced and @legacy_replaced"
        self.assertEqual(perform_replacements(text, task), expected)

    def test_partial_match_user(self):
        task = {
            'replacements': [{'type': 'user', 'find': '@old', 'replace': '@new'}]
        }
        text = "Hello @older @old"
        expected = "Hello @older @new"
        self.assertEqual(perform_replacements(text, task), expected)
        
    def test_case_insensitive(self):
        task = {
            'replacements': [{'type': 'user', 'find': '@OLD', 'replace': '@new'}]
        }
        text = "Hello @old"
        expected = "Hello @new"
        self.assertEqual(perform_replacements(text, task), expected)

if __name__ == '__main__':
    unittest.main()
