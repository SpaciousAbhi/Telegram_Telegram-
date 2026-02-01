# Telegram Userbot Forwarder

A deploy-ready Telegram Userbot that monitors public channels and forwards posts to a target channel with configurable replacements for usernames and links.

## Features

-   **Monitor Public Channels**: Listens for new messages in specified source channels.
-   **Intelligent Replacements**: Automatically replaces specific usernames and `t.me` links with your own before forwarding.
-   **Persistent Configuration**: Saves your task list to your "Saved Messages" on Telegram, so you never lose your settings, even on ephemeral hosting like Heroku.
-   **Chat-based Management**: Manage tasks entirely through Telegram "Saved Messages" commands (`/add`, `/list`, `/del`).
-   **Auto-Join**: Automatically joins source channels to ensure reliable monitoring.

## Deployment

### Prerequisites

1.  **Telegram API Credentials**: Get your `API_ID` and `API_HASH` from [https://my.telegram.org/](https://my.telegram.org/).
2.  **Session String**: You need to generate a Telethon session string. Run the provided helper script locally (if you have Python installed) or use an online generator.

    *To generate locally:*
    ```bash
    pip install telethon
    python3 -c "from telethon.sync import TelegramClient; from telethon.sessions import StringSession; print(TelegramClient(StringSession(), 'YOUR_API_ID', 'YOUR_API_HASH').start().session.save())"
    ```

### Heroku Deployment

1.  **Create a new app** on Heroku.
2.  **Go to Settings > Config Vars**.
3.  Add the following variables:
    -   `API_ID`: Your App ID.
    -   `API_HASH`: Your App Hash.
    -   `SESSION_STRING`: The long string you generated above.
4.  **Deploy** the code (connect GitHub or push via CLI).
5.  **Go to Resources** and turn on the `worker` dyno.

## Usage

Once the bot is running, open your **Saved Messages** on Telegram (the chat with yourself).

### Commands

-   **`/help`**: Show the help message.
-   **`/list`**: List all active monitoring tasks.
-   **`/del <ID>`**: Delete a task by its ID (found in `/list`).
-   **`/add`**: Add a new task. You can copy-paste the template below:

```text
/add
source: @SourceChannel
target: @MyTargetChannel
find_user: @OriginalUser
replace_user: @MyUser
find_link: original_link
replace_link: my_link
```

*Note: `find_user`/`replace_user` and `find_link`/`replace_link` are optional. If omitted, no replacements will occur for that specific category.*

### Task Fields

-   `source`: The public channel username to monitor (e.g., `@BBCNews`).
-   `target`: The channel where modified messages will be sent (e.g., `@MyNewsFeed`).
-   `find_user`: The specific username mention to look for (e.g., `@admin`).
-   `replace_user`: What to replace it with (e.g., `@support`).
-   `find_link`: A partial or full link to look for.
-   `replace_link`: The replacement link.

## Logic Details

-   **Persistence**: The bot checks "Saved Messages" for a pinned message containing your config. If it doesn't exist, it creates one. Do not delete this message if you want to keep your tasks!
-   **Membership**: When you add a task, the userbot will attempt to join the source channel if it is not already a member.
