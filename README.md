# Enterprise Telegram Forwarder

A professional-grade Telegram Userbot + Controller Bot that monitors channels and forwards messages with advanced replacement rules, log reporting, and a GUI management interface.

## Features

-   **Hybrid Architecture**:
    -   **Userbot**: Monitors public channels, joins them, and forwards messages.
    -   **Controller Bot**: A friendly UI bot for managing tasks, settings, and rules.
-   **Live & Historical**: Supports real-time monitoring and background backfill.
-   **Inline UI**: Manage everything via buttons (No text commands needed).
-   **Advanced Replacements**:
    -   Global Regex-based text replacements.
    -   Link Stripping (removes hyperlinks and their text).
-   **Logging**: Reports every action (Success/Failure/Changes) to a Log Channel.
-   **Persistence**: SQLite database stores all tasks and settings.

## Deployment

### Prerequisites

1.  **Telegram API Credentials**: Get `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org/).
2.  **Userbot Session**: Generate a `SESSION_STRING` using `Telethon`.
3.  **Controller Bot Token**: Create a new bot with [@BotFather](https://t.me/BotFather) and get the `BOT_TOKEN`.

### Heroku Deployment

1.  **Create a new app** on Heroku.
2.  **Go to Settings > Config Vars**.
3.  Add the following variables:
    -   `API_ID`: Your App ID.
    -   `API_HASH`: Your App Hash.
    -   `SESSION_STRING`: Your Userbot Session String.
    -   `BOT_TOKEN`: Your Controller Bot Token (NEW!).
4.  **Deploy** the code.
5.  **Turn on the Worker**: Go to Resources and enable `worker`.

## Usage

1.  Start the **Controller Bot** in Telegram (`/start`).
2.  Use the menu to:
    -   **Set Log Channel**: Where reports will be sent.
    -   **Set Replacements**: Configure global rules.
    -   **Create Task**: Start monitoring a source channel.

## Troubleshooting

-   **Crash on Start?** Check your Config Vars. If `BOT_TOKEN` is missing, the bot will crash.
-   **Not Joining?** Ensure the Userbot account has space to join new channels (limit is 500).
