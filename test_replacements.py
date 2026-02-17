import unittest
import sys
from unittest.mock import MagicMock

# Mock telethon imports required by utils.py
sys.modules['telethon'] = MagicMock()
sys.modules['telethon.errors'] = MagicMock()
sys.modules['telethon.tl'] = MagicMock()
sys.modules['telethon.tl.functions'] = MagicMock()
sys.modules['telethon.tl.functions.channels'] = MagicMock()
sys.modules['telethon.tl.types'] = MagicMock()

from utils import perform_replacements

class TestReplacements(unittest.TestCase):
    def test_basic_replacement(self):
        task = {
            'find_user': '@old',
            'replace_user': '@new',
            'find_link': 't.me/old',
            'replace_link': 't.me/new'
        }
        
        text = "Hello @old check t.me/old"
        expected = "Hello @new check t.me/new"
        self.assertEqual(perform_replacements(text, task), expected)

    def test_partial_match_user(self):
        task = {
            'find_user': '@old',
            'replace_user': '@new'
        }
        
        # Should NOT replace @older
        text = "Hello @older @old"
        expected = "Hello @older @new"
        self.assertEqual(perform_replacements(text, task), expected)
        
    def test_case_insensitive(self):
        task = {
            'find_user': '@OLD',
            'replace_user': '@new'
        }
        
        text = "Hello @old"
        expected = "Hello @new"
        self.assertEqual(perform_replacements(text, task), expected)

    def test_link_boundaries(self):
        task = {
            'find_link': 't.me/link',
            'replace_link': 't.me/new'
        }
        
        # Should NOT replace t.me/link2
        text = "Click t.me/link2 or t.me/link"
        expected = "Click t.me/link2 or t.me/new"
        self.assertEqual(perform_replacements(text, task), expected)

if __name__ == '__main__':
    unittest.main()
