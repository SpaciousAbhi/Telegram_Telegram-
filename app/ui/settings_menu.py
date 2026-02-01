from telethon import Button
from app.database.db import get_db
from app.database.models import GlobalSettings

class SettingsMenu:

    @staticmethod
    def get_settings_menu():
        """Main settings dashboard."""
        return [
            [Button.inline("📝 Edit Replacements", b"settings_replacements")],
            [Button.inline("📊 Set Log Channel", b"settings_log_channel")],
            [Button.inline("🔙 Back", b"back_to_main")]
        ]

    @staticmethod
    def replacement_controls():
        """Controls for adding/listing replacements."""
        return [
            [Button.inline("➕ Add Rule", b"add_rule"), Button.inline("📋 List Rules", b"list_rules")],
            [Button.inline("🔙 Back to Settings", b"settings")]
        ]
