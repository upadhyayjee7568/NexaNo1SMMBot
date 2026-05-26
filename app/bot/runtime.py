from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.core.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "Welcome to Nexa SMM Panel 🚀\n"
    "Fast, secure, and reliable social media growth services.\n"
    "✅ Instant Order Processing\n"
    "✅ Secure Payments (Cashfree)\n"
    "✅ 24×7 Support\n"
    "Start here: /start"
)


async def _is_member(context: ContextTypes.DEFAULT_TYPE, chat_id: str, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in {"member", "administrator", "creator"}
    except Exception:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.effective_chat:
        return

    user_id = update.effective_user.id

    if settings.telegram_force_join_enabled:
        channel_ok = await _is_member(context, settings.telegram_updates_channel, user_id)
        group_ok = await _is_member(context, settings.telegram_discussion_group, user_id)

        if not (channel_ok and group_ok):
            kb = [
                [InlineKeyboardButton("Join Updates Channel", url=settings.telegram_updates_channel)],
                [InlineKeyboardButton("Join Community Group", url=f"https://t.me/{settings.telegram_discussion_group.lstrip('@')}")],
            ]
            await update.message.reply_text(
                "Access required before using bot:\n1) Join channel\n2) Join group\n3) Run /start again",
                reply_markup=InlineKeyboardMarkup(kb),
            )
            return

    await update.message.reply_text(WELCOME_TEXT)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Commands:\n"
        "/start - Start bot\n"
        "/help - Help menu\n"
        "/support - Support contact\n"
        "/wallet - Wallet API endpoint info"
    )


async def support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Support: @{settings.telegram_support_username.lstrip('@')}")


async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id if update.effective_user else 0
    await update.message.reply_text(
        f"Wallet check API: GET /api/wallet/{user_id}\n"
        "(Integrate this in bot UI next phase for live balance button)"
    )


def build_application() -> Application:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("support", support))
    app.add_handler(CommandHandler("wallet", wallet))
    return app


def run_polling() -> None:
    app = build_application()
    logger.info("Starting Nexa Telegram bot polling runtime")
    app.run_polling(close_loop=False)
