from telethon import events
from app.ui.menu_builder import MenuBuilder

@events.register(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """
    Shows the main dashboard.
    """
    # Only allow the userbot owner (me) to interact
    if not event.out and not event.sender_id == (await event.client.get_me()).id:
        return

    text = (
        "**🤖 Ultimate Forwarder Bot**\n\n"
        "Welcome to your personal automation hub.\n"
        "Manage your forwarding tasks with ease."
    )

    await event.respond(text, buttons=MenuBuilder.main_menu())
