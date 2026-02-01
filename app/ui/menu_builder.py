from telethon import Button

class MenuBuilder:
    """
    Helper class to build Telethon Inline Keyboards.
    """

    @staticmethod
    def main_menu():
        return [
            [Button.inline("➕ Create New Task", b"create_task")],
            [Button.inline("📂 My Tasks", b"list_tasks"), Button.inline("⚙️ Settings", b"settings")],
            [Button.inline("❓ Help / Status", b"help")]
        ]

    @staticmethod
    def cancel_button():
        return [Button.inline("❌ Cancel", b"cancel_action")]

    @staticmethod
    def back_button(data):
        return [Button.inline("🔙 Back", data)]

    @staticmethod
    def confirmation_menu(action_data):
        return [
            [Button.inline("✅ Yes", action_data), Button.inline("❌ No", b"cancel_action")]
        ]

    @staticmethod
    def task_controls(task_id):
        tid = str(task_id).encode()
        return [
            [Button.inline("⏸ Pause", b"pause_" + tid), Button.inline("▶️ Resume", b"resume_" + tid)],
            [Button.inline("✏️ Edit", b"edit_" + tid), Button.inline("🗑 Delete", b"delete_" + tid)],
            [Button.inline("🔙 Back to List", b"list_tasks")]
        ]

    @staticmethod
    def task_edit_menu(task_id):
        tid = str(task_id).encode()
        return [
            [Button.inline("Change Source", b"edit_source_" + tid)],
            [Button.inline("Change Target", b"edit_target_" + tid)],
            [Button.inline("🔙 Back to Task", b"view_task_" + tid)]
        ]

    @staticmethod
    def config_toggles(current_config):
        """
        Dynamic menu for toggling settings during Wizard.
        """
        # Example config: {'strip_links': False, 'strip_captions': False}
        strip_links = "✅" if current_config.get('strip_links') else "❌"
        strip_captions = "✅" if current_config.get('strip_captions') else "❌"

        return [
            [
                Button.inline(f"Strip Links: {strip_links}", b"toggle_strip_links"),
                Button.inline(f"Strip Captions: {strip_captions}", b"toggle_strip_captions")
            ],
            [Button.inline("✅ Done & Save", b"save_task")]
        ]
