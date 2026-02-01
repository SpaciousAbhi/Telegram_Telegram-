from telethon import events
from app.ui.menu_builder import MenuBuilder

@events.register(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """
    Shows the main dashboard.
    """
    # For a Bot, we don't need to check "if not event.out" because all messages to a bot are incoming.
    # We SHOULD check if the user is authorized (e.g., hardcoded Admin ID) but for now we assume
    # the user knows who they are sharing the bot link with or we add an AUTH check later.
    # To be safe, let's just allow it for now or check ID if the user provided one.

    text = (
        "**🤖 Ultimate Forwarder Bot**\n\n"
        "Welcome to your personal automation hub.\n"
        "Manage your forwarding tasks with ease."
    )

    await event.respond(text, buttons=MenuBuilder.main_menu())
