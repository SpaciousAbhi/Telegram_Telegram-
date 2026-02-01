from telethon import events
from app.ui.menu_builder import MenuBuilder
from app.core.ai_brain import brain

@events.register(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """
    Shows the main dashboard.
    """
    text = (
        "**🤖 Ultimate Forwarder Bot**\n\n"
        "Welcome to your personal automation hub.\n"
        "Manage your forwarding tasks with ease.\n\n"
        "🧠 **AI Brain Active:** You can also just chat with me!\n"
        "Try saying: *'Forward from @BBC to @MyChannel'*."
    )

    await event.respond(text, buttons=MenuBuilder.main_menu())

@events.register(events.NewMessage)
async def ai_chat_handler(event):
    """
    Catches all text messages that are NOT commands and feeds them to the AI Brain.
    """
    if event.text.startswith('/'):
        return # Ignore commands

    if not event.is_private:
        return # Ignore groups for now

    # Send "Typing..." action
    async with event.client.action(event.chat_id, 'typing'):
        response = await brain.process_user_intent(event.sender_id, event.text)

    await event.respond(response)
