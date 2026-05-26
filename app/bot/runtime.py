from __future__ import annotations

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from app.core.settings import settings
from app.db.session import SessionLocal
from app.db.models import ServiceCatalog, User
from app.services.wallet import wallet_balance
from app.services.tickets import create_ticket
from app.services.growth import credit_daily_reward, register_referral

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
    "Use /menu to open panel"
)

ORDER_SERVICE, ORDER_LINK, ORDER_QTY = range(3)
TICKET_SUBJECT, TICKET_MESSAGE = range(3, 5)

    "Start here: /start"
)


async def _is_member(context: ContextTypes.DEFAULT_TYPE, chat_id: str, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in {"member", "administrator", "creator"}
    except Exception:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user:
        return
    if not update.effective_user or not update.effective_chat:
        return

    user_id = update.effective_user.id

    if settings.telegram_force_join_enabled:
        channel_ok = await _is_member(context, settings.telegram_updates_channel, user_id)
        group_ok = await _is_member(context, settings.telegram_discussion_group, user_id)
        if not (channel_ok and group_ok):
            kb = [[InlineKeyboardButton("Join Updates", url=settings.telegram_updates_channel)],
                  [InlineKeyboardButton("Join Group", url=f"https://t.me/{settings.telegram_discussion_group.lstrip('@')}")]]
            await update.message.reply_text("Join channel + group then /start again", reply_markup=InlineKeyboardMarkup(kb))
            return

    await update.message.reply_text(WELCOME_TEXT)
    await menu(update, context)


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    kb = [
        [InlineKeyboardButton("🛒 Place Order", callback_data="menu_order")],
        [InlineKeyboardButton("💰 Wallet", callback_data="menu_wallet")],
        [InlineKeyboardButton("🎟 Ticket Support", callback_data="menu_ticket")],
        [InlineKeyboardButton("🎁 Daily Reward", callback_data="menu_reward")],
        [InlineKeyboardButton("👥 Referral", callback_data="menu_referral")],
    ]
    if update.message:
        await update.message.reply_text("Main Menu", reply_markup=InlineKeyboardMarkup(kb))
    elif update.callback_query:
        await update.callback_query.message.reply_text("Main Menu", reply_markup=InlineKeyboardMarkup(kb))


async def menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    d = q.data
    if d == "menu_wallet":
        await wallet(update, context)
    elif d == "menu_order":
        await q.message.reply_text("Send platform name (Instagram/YouTube/Telegram/Facebook):")
        context.user_data["order"] = {}
        return ORDER_SERVICE
    elif d == "menu_ticket":
        await q.message.reply_text("Send ticket subject:")
        return TICKET_SUBJECT
    elif d == "menu_reward":
        await daily_reward(update, context)
    elif d == "menu_referral":
        await referral(update, context)


async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id if update.effective_user else 0
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.telegram_id == uid).first()
        bal = "0.00" if not u else str(wallet_balance(db, u.id))
    finally:
        db.close()
    msg = f"Wallet Balance: ₹{bal}"
    if update.callback_query:
        await update.callback_query.message.reply_text(msg)
    else:
        await update.message.reply_text(msg)


async def order_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    platform = update.message.text.strip()
    db = SessionLocal()
    try:
        services = db.query(ServiceCatalog).filter(ServiceCatalog.platform.ilike(platform), ServiceCatalog.enabled == True).limit(10).all()  # noqa
        if not services:
            await update.message.reply_text("No services found. Try exact platform name.")
            return ORDER_SERVICE
        context.user_data["order"]["platform"] = platform
        context.user_data["order"]["services"] = [s.id for s in services]
        msg = "Select service ID and send it:\n" + "\n".join([f"{s.id}: {s.service_name} (₹{s.base_rate})" for s in services])
        await update.message.reply_text(msg)
    finally:
        db.close()
    return ORDER_LINK


async def order_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if context.user_data.get("order", {}).get("service_id") is None:
        if not text.isdigit():
            await update.message.reply_text("Send valid numeric service ID")
            return ORDER_LINK
        sid = int(text)
        if sid not in context.user_data["order"].get("services", []):
            await update.message.reply_text("Service ID not in list. Try again.")
            return ORDER_LINK
        context.user_data["order"]["service_id"] = sid
        await update.message.reply_text("Now send target link:")
        return ORDER_LINK

    context.user_data["order"]["link"] = text
    await update.message.reply_text("Now send quantity:")
    return ORDER_QTY


async def order_qty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.message.text.strip()
    if not q.isdigit():
        await update.message.reply_text("Quantity must be number")
        return ORDER_QTY
    data = context.user_data.get("order", {})
    await update.message.reply_text(
        f"Order captured ✅\nPlatform: {data.get('platform')}\nService ID: {data.get('service_id')}\nLink: {data.get('link')}\nQty: {q}\nUse API /api/orders/place for execution (already wired)."
    )
    context.user_data.pop("order", None)
    return ConversationHandler.END


async def ticket_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["ticket_subject"] = update.message.text.strip()
    await update.message.reply_text("Send ticket message:")
    return TICKET_MESSAGE


async def ticket_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    subject = context.user_data.get("ticket_subject", "Support")
    body = update.message.text.strip()
    uid = update.effective_user.id
    db = SessionLocal()
    try:
        t = create_ticket(db, uid, subject, body)
    finally:
        db.close()
    await update.message.reply_text(f"Ticket created: {t.ticket_ref}")
    return ConversationHandler.END


async def daily_reward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    db = SessionLocal()
    try:
        status = credit_daily_reward(db, uid)
    finally:
        db.close()
    await (update.callback_query.message.reply_text if update.callback_query else update.message.reply_text)(f"Daily reward: {status}")


async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    await (update.callback_query.message.reply_text if update.callback_query else update.message.reply_text)(
        f"Referral link format: /refer {uid}\nNew user runs: /start <referrer_id>"
    )


async def refer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /refer <referrer_telegram_id>")
        return
    referrer = int(context.args[0])
    referred = update.effective_user.id
    db = SessionLocal()
    try:
        status = register_referral(db, referrer, referred)
    finally:
        db.close()
    await update.message.reply_text(f"Referral register status: {status}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Commands: /start /menu /wallet /reward /refer /support")


async def support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Support: @{settings.telegram_support_username.lstrip('@')}")



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
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("support", support))
    app.add_handler(CommandHandler("wallet", wallet))
    app.add_handler(CommandHandler("reward", daily_reward))
    app.add_handler(CommandHandler("refer", refer_cmd))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_click, pattern="^menu_order$")],
        states={
            ORDER_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_service)],
            ORDER_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_link)],
            ORDER_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_qty)],
        },
        fallbacks=[],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_click, pattern="^menu_ticket$")],
        states={
            TICKET_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ticket_subject)],
            TICKET_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ticket_message)],
        },
        fallbacks=[],
    ))

    app.add_handler(CallbackQueryHandler(menu_click, pattern="^menu_(wallet|reward|referral)$"))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("support", support))
    app.add_handler(CommandHandler("wallet", wallet))
    return app


def run_polling() -> None:
    app = build_application()
    logger.info("Starting Nexa Telegram bot polling runtime")
    app.run_polling(close_loop=False)
