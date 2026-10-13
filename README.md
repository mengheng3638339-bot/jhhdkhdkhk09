# Telegram Customer File Delivery Bot

A Telegram bot for sending messages, photos, and documents from an authorized support account to customers. The owner can also publish photos and documents in a shared catalog for customers to browse and request. The default local setup stores the catalog in SQLite; the Vercel webhook setup uses PostgreSQL. Uploaded media itself is kept by Telegram.

## Setup

1. Create a bot with [BotFather](https://t.me/BotFather) and copy its token.
2. Find the numeric Telegram user ID of the support account that may send files.
3. Install Python 3.10 or newer.
4. Create and activate a virtual environment, then install dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

5. Copy `.env.example` to `.env`, then set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ADMIN_ID` to the real values. Keep the real values only in `.env`; do not put them in `.env.example`.
6. Start the bot:

   ```powershell
   py bot.py
   ```

   The bot loads `.env` from the same folder as `bot.py`, regardless of the current working directory. Values in `.env` take precedence over stale environment variables from another bot configuration.

## Deploy as a Vercel webhook

The bot can also run as a Python webhook function on Vercel. Unlike polling, this mode needs a public HTTPS endpoint and a persistent PostgreSQL database; Vercel's local filesystem is not used for catalog data or user interaction state.

1. Create a managed PostgreSQL database and copy its SSL-enabled connection URL.
2. Import this repository into Vercel. The `api` functions and `requirements.txt` are detected as the deployment entry points.
3. In the Vercel project's **Settings → Environment Variables**, set:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_ADMIN_ID`
   - `TELEGRAM_WEBHOOK_SECRET` — generate a random value containing only letters, numbers, `_`, or `-` (for example, with `python -c "import secrets; print(secrets.token_urlsafe(32))"`).
   - `DATABASE_URL` — the PostgreSQL connection URL from step 1.
4. Deploy the project, then configure Telegram to send updates to the deployed `/api` endpoint. On a computer with Python and this project's dependencies installed, put the bot token and the same webhook secret in the local `.env` file and run:

   ```powershell
   py set_webhook.py https://your-project.vercel.app
   ```

   Use the deployment's HTTPS origin, without `/api`. Stop any local `py bot.py` polling process first; Telegram cannot deliver updates to polling and a webhook at the same time.
5. If you want to keep the catalog in the existing local `file_catalog.sqlite3`, temporarily add `DATABASE_URL` with the same PostgreSQL URL to your local `.env`, then run `py migrate_catalog.py` once before users start using the deployed bot. Remove the URL from `.env` afterward if it is not needed locally. The migration copies catalog entries, known users, and bans; it does not copy files already stored by Telegram.

Telegram updates are checked against `TELEGRAM_WEBHOOK_SECRET`. The bot persists its pending upload/delivery state in PostgreSQL so it survives separate function invocations. `/view` and `/previewht` create one-hour public links backed by PostgreSQL; anyone holding a link can open its page before it expires. Keep the database URL and bot token out of Git.

## Deliver a file

1. The customer must open the bot and send `/start` before the bot can message them.
2. The customer can share their numeric Telegram ID with support. The owner can use `/id` to list usernames and IDs for users known to the bot.
3. To send a text message, the authorized admin sends `/message <customer_telegram_id> <message>` in a private chat with the bot.
4. To send media, the admin sends `/send <customer_telegram_id>`, then uploads one photo or document.
5. The bot reports whether Telegram accepted the delivery. Send `/cancel` to cancel a pending media delivery.

The customer command menu shows `/start`, `/help`, `/files`, `/file`, `/upload`, `/done`, `/view`, and `/viewht`. The owner also has `/id` to list known users with IDs, `/listname` to list their names and usernames, `/ban`, and `/unban`, plus `/pending` to review submissions and `/previewht` to open an approved HTML preview on a phone over Wi-Fi or mobile data. These lists include users who interact with the bot and existing catalog uploaders; they cannot show Telegram users who have never interacted with the bot. `/upload` starts a session that accepts multiple files; send `/done` when finished or `/cancel` to stop. `/files` shows clickable buttons for approved catalog items; `/view` creates temporary HTTPS browser links for approved HTML files; `/viewht` sends HTML files as downloads.

The owner can use `/ban <telegram_user_id>` to block an account from interacting with the bot, and `/unban <telegram_user_id>` to restore access. These bot-level bans persist across restarts in the local SQLite catalog or the Vercel PostgreSQL database; they do not ban users from Telegram groups.

## Shared customer file catalog

1. Any user sends `/upload` in a private chat, then uploads one or more Telegram **documents** (each filename is its catalog name) or **photos with captions** (each caption is its name). Send `/done` to finish the upload session, or `/cancel` to stop.
2. The upload stays out of the shared catalog until the owner approves it. The owner uses `/pending`, then taps **Approve** or **Reject**. Users can cancel an upload with `/cancel` before sending the media.
3. Approved files appear in `/files`. Users tap a file button to receive it, or use `/file <file_name>` to request it by name. For names with spaces, include the full name, for example `/file Product Guide.pdf`.
4. The owner can upload directly; owner uploads are approved immediately and replace a catalog entry with the same name.
5. The owner can use `/delete`, select a catalog entry, and confirm to remove it from the bot's catalog. The **Delete all files** button removes every entry, including pending submissions, after a separate confirmation. These actions do not remove copies already sent in Telegram chats.
6. Any user can use `/view` and tap an approved `.html` or `.htm` button to open the page in a phone browser, including over 4G. Local polling uses Cloudflare Quick Tunnels; Vercel mode serves the preview through an expiring route backed by PostgreSQL. Anyone with a link can access that HTML page; share links only with intended viewers.
7. `/viewht <file_name>` sends a specific approved HTML file as a download. The owner can use `/previewht` or `/previewht <file_name>` to create a temporary public HTTPS preview link. Local polling needs the bot and Cloudflare Quick Tunnel running; Vercel mode uses its public preview route. Anyone with the link can view the page until it expires, so share it only with intended viewers. Telegram does not run interactive HTML inside a chat; a Telegram Web App still requires a public HTTPS URL.

In local polling mode, catalog entries persist in `file_catalog.sqlite3` beside `bot.py`; this file is ignored by Git. In Vercel mode, catalog entries and bans persist in PostgreSQL.

Only the configured admin user ID can start a delivery. Customer IDs must be positive numeric Telegram user IDs. Telegram may reject files that exceed its current bot API limits or chats that have not started the bot.

# ffgghh
