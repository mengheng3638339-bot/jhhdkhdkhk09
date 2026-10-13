import asyncio
import os
import re
import sys
from urllib.parse import urlsplit

from telegram import Bot

from bot import get_config


async def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: py set_webhook.py https://your-project.vercel.app")

    deployment_url = sys.argv[1].strip().rstrip("/")
    parsed_url = urlsplit(deployment_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc or parsed_url.path:
        raise SystemExit("Provide the HTTPS origin of your Vercel deployment, without a path.")

    token, _ = get_config()
    secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", secret):
        raise SystemExit("TELEGRAM_WEBHOOK_SECRET must use 1-256 letters, digits, underscores, or hyphens.")

    bot = Bot(token)
    await bot.initialize()
    try:
        await bot.set_webhook(
            url=f"{deployment_url}/api",
            secret_token=secret,
            drop_pending_updates=False,
        )
    finally:
        await bot.shutdown()

    print(f"Webhook configured for {deployment_url}/api")


if __name__ == "__main__":
    asyncio.run(main())
