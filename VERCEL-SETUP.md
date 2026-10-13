# Deploy this Telegram bot to Vercel

## Before deploying
- Rotate the Telegram bot token in @BotFather if the old token was ever included in a shared ZIP, GitHub repository, screenshot, or message.
- This project needs a managed PostgreSQL database for Vercel. Vercel's filesystem is not persistent.

## GitHub files
Upload these files and folders to the repository root:
- `api/index.py`
- `bot.py`
- `database.py`
- `requirements.txt`
- `vercel.json`
- `set_webhook.py`
- `migrate_catalog.py` (only needed if migrating local catalog data)

Do not upload `.env`, virtual-environment files, executables, or `file_catalog.sqlite3`.

## Vercel environment variables
In Vercel → Project → Settings → Environment Variables, add these four variables for Production (and Preview if needed):

1. `TELEGRAM_BOT_TOKEN` — token from @BotFather
2. `TELEGRAM_ADMIN_ID` — your numeric Telegram user ID
3. `TELEGRAM_WEBHOOK_SECRET` — a random string using only A-Z, a-z, 0-9, `_`, and `-`, 1–256 characters
4. `DATABASE_URL` — SSL-enabled PostgreSQL connection URL from your database provider

Save the variables, then redeploy.

## Webhook URL
After deployment, your endpoint is:
`https://YOUR-PROJECT.vercel.app/api`

Install the project requirements on a computer with Python, create a local `.env` containing the same `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_ID`, and `TELEGRAM_WEBHOOK_SECRET`, then run:

`python set_webhook.py https://YOUR-PROJECT.vercel.app`

Pass only the HTTPS origin to the script (no `/api`). It appends `/api` itself. Stop any polling instance of the bot first; Telegram cannot use polling and a webhook simultaneously.

## Verify
Open `https://YOUR-PROJECT.vercel.app/api` in a browser. The health route should return JSON showing the webhook is ready. Then send `/start` to your bot. If it fails, check Vercel → Logs and Telegram `getWebhookInfo`.
