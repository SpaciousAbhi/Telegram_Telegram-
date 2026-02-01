import unittest
from app.core.transformer import ContentTransformer

class TestTransformer(unittest.TestCase):
    def test_strip_links(self):
        text = "Hello check http://bad.com and https://test.org"
        config = {'strip_links': True}

        new_text, logs = ContentTransformer.apply_replacements(text, [], config)

        self.assertEqual(new_text, "Hello check  and")
        self.assertTrue(len(logs) > 0)

    def test_regex_replacement(self):
        text = "Follow @bad_user and join"
        global_rules = [{'find': '@bad_user', 'replace': '@good_user'}]

        new_text, logs = ContentTransformer.apply_replacements(text, [], {}, global_settings=global_rules)

        self.assertEqual(new_text, "Follow @good_user and join")
        self.assertIn("Replaced '@bad_user' -> '@good_user'", logs)

    def test_deletion(self):
        text = "Click here to win!"
        # Replacement is blank string
        global_rules = [{'find': 'Click here', 'replace': ''}]

        new_text, logs = ContentTransformer.apply_replacements(text, [], {}, global_settings=global_rules)

        self.assertEqual(new_text, "to win!")

if __name__ == '__main__':
    unittest.main()
