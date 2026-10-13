import asyncio
import hmac
import logging
import os
import re

from fastapi import FastAPI, HTTPException, Request
from telegram import Update

from bot import (
    create_application,
    get_config,
    get_persistent_user_state,
    initialize_catalog,
    save_persistent_user_state,
)


logger = logging.getLogger(__name__)
app = FastAPI()
_request_lock = asyncio.Lock()
_database_initialized = False
_commands_configured = False


@app.get("/")
async def health_check() -> dict[str, str]:
    return {"status": "Telegram webhook is ready"}


@app.post("/")
async def telegram_webhook(request: Request) -> dict[str, bool]:
    global _database_initialized, _commands_configured

    token, admin_id = get_config()
    secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", secret):
        raise HTTPException(status_code=503, detail="Webhook secret is not configured correctly.")
    supplied_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not hmac.compare_digest(supplied_secret, secret):
        raise HTTPException(status_code=403, detail="Invalid webhook secret.")

    try:
        update_data = await request.json()
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Invalid Telegram update JSON.") from error
    if not isinstance(update_data, dict):
        raise HTTPException(status_code=400, detail="Telegram update must be a JSON object.")

    async with _request_lock:
        if not _database_initialized:
            initialize_catalog()
            _database_initialized = True

        application = create_application(token, admin_id)
        await application.initialize()
        try:
            if not _commands_configured:
                from bot import configure_commands

                await configure_commands(application)
                _commands_configured = True

            await application.start()
            update = Update.de_json(update_data, application.bot)
            user = update.effective_user
            if user is not None:
                application.user_data[user.id].update(get_persistent_user_state(user.id))

            await application.process_update(update)

            if user is not None:
                save_persistent_user_state(user.id, application.user_data[user.id])
        except Exception:
            logger.exception("Failed to process a Telegram webhook update.")
            raise
        finally:
            if application.running:
                await application.stop()
            await application.shutdown()

    return {"ok": True}
