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

        # --- A. Global Replacements & Filters ---
        for rule in rules:
            find_pattern = rule.get('find')
            replace_with = rule.get('replace', '')

            if not find_pattern: continue

            try:
                # 1. SKIP MESSAGE Filter (Special Flag: 'SKIP_MESSAGE')
                if replace_with.strip() == 'SKIP_MESSAGE':
                    if re.search(re.escape(find_pattern), text, re.IGNORECASE):
                        log_summary.append(f"Skipped message containing '{find_pattern}'")
                        return None, log_summary # Return None to signal skip

                # 2. DELETE LINE Filter (Special Flag: 'DELETE_LINE')
                elif replace_with.strip() == 'DELETE_LINE':
                    lines = text.split('\n')
                    new_lines = []
                    for line in lines:
                        if re.search(re.escape(find_pattern), line, re.IGNORECASE):
                            log_summary.append(f"Deleted line containing '{find_pattern}'")
                        else:
                            new_lines.append(line)
                    text = '\n'.join(new_lines)

                # 3. Standard Replacement
                else:
                    pattern = re.compile(re.escape(find_pattern), re.IGNORECASE)
                    if pattern.search(text):
                        text = pattern.sub(replace_with, text)
                        log_summary.append(f"Replaced '{find_pattern}' -> '{replace_with}'")

            except Exception as e:
                logger.error(f"Rule error {find_pattern}: {e}")

        # --- B. Config: Strip Links (Naive) ---
        if config.get('strip_links'):
            url_pattern = r'https?://\S+|www\.\S+'
            matches = re.findall(url_pattern, text)
            if matches:
                text = re.sub(url_pattern, '', text)
                log_summary.append(f"Stripped {len(matches)} links.")

        return text.strip(), log_summary
