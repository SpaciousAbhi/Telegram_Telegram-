import re
import logging
import json
from telethon import Button

logger = logging.getLogger(__name__)

class ContentTransformer:
    """
    Handles content modification logic (Regex, Entity Stripping, etc.)
    """

    @staticmethod
    def apply_replacements(text, entities, config, global_settings=None):
        """
        Applies rules to text and entities.
        Returns (modified_text, log_summary)

        global_settings: List of dicts [{'find': '...', 'replace': '...'}]
        """
        if not text:
            return text, []

        log_summary = []

        # 0. Load Global Rules if passed as raw list or None
        rules = global_settings if global_settings else []

        # 1. Hyperlink Removal (Entity Stripping) - Advanced
        # We process this first because removing text changes indices for regex
        # However, regex is easier to run on the whole text first if we are just string replacing.
        # But if we delete a chunk, regex indices break.
        # Strategy: Run simple regex replacements first (Usernames/Links in text),
        # THEN run entity stripping? Or vice versa?
        # Let's do Regex First (Modify text), then strip entities if they match rules.

        # --- A. Global Regex Replacements ---
        for rule in rules:
            find_pattern = rule.get('find')
            replace_with = rule.get('replace', '')

            if not find_pattern:
                continue

            # Create safe regex
            # If user provided a regex (starts with r'..') use it, else escape
            # For simplicity, we treat everything as literal string match unless it looks like regex
            # But "looks like regex" is risky. Let's do literal case-insensitive replace for now
            # OR simple regex for words.

            try:
                # Case insensitive find
                pattern = re.compile(re.escape(find_pattern), re.IGNORECASE)

                # Check if present
                if pattern.search(text):
                    text = pattern.sub(replace_with, text)
                    log_summary.append(f"Replaced '{find_pattern}' -> '{replace_with}'")
            except Exception as e:
                logger.error(f"Regex error for rule {find_pattern}: {e}")

        # --- B. Config: Strip Links (Naive) ---
        if config.get('strip_links'):
            url_pattern = r'https?://\S+|www\.\S+'
            matches = re.findall(url_pattern, text)
            if matches:
                text = re.sub(url_pattern, '', text)
                log_summary.append(f"Stripped {len(matches)} links.")

        return text.strip(), log_summary
