"""Serverless Telegram bot (webhook mode).

Vercel is serverless, so the classic always-on polling bot cannot run. Instead Telegram
POSTs each update to ``/api/telegram/webhook`` and this module handles it statelessly.
Multi-step conversation state is persisted in the ``bot_state`` table because the
process does not survive between requests.
"""

from __future__ import annotations

import json
import logging
from decimal import Decimal, InvalidOperation

import httpx
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.models import BotState, Order, ServiceCatalog, User
from app.services import cashfree as cashfree_svc
from app.services import upi_fallback
from app.services.growth import credit_daily_reward, register_referral
from app.services.tickets import create_ticket
from app.services.wallet import wallet_balance

logger = logging.getLogger("nexa.bot")

API = "https://api.telegram.org/bot{token}/{method}"


# ----------------------------- Telegram API helpers -----------------------------
async def _call(method: str, payload: dict) -> dict:
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set")
        return {}
    url = API.format(token=settings.telegram_bot_token, method=method)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload)
            return resp.json()
    except httpx.HTTPError as exc:
        logger.error("Telegram API error on %s: %s", method, exc)
        return {}


async def send_message(chat_id: int, text: str, keyboard: list | None = None, parse_mode: str | None = "HTML") -> dict:
    payload: dict = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if keyboard is not None:
        payload["reply_markup"] = {"inline_keyboard": keyboard}
    return await _call("sendMessage", payload)


async def send_photo_bytes(chat_id: int, png: bytes, caption: str = "") -> dict:
    if not settings.telegram_bot_token:
        return {}
    url = API.format(token=settings.telegram_bot_token, method="sendPhoto")
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                url,
                data={"chat_id": str(chat_id), "caption": caption, "parse_mode": "HTML"},
                files={"photo": ("upi-qr.png", png, "image/png")},
            )
            return resp.json()
    except httpx.HTTPError as exc:
        logger.error("Telegram sendPhoto error: %s", exc)
        return {}


async def answer_callback(callback_id: str, text: str = "") -> None:
    await _call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text})


# ----------------------------- State helpers -----------------------------
def _get_state(db: Session, tg_id: int) -> BotState | None:
    return db.query(BotState).filter(BotState.telegram_id == tg_id).first()


def _set_state(db: Session, tg_id: int, flow: str | None, step: str | None, data: dict | None = None) -> None:
    st = _get_state(db, tg_id)
    if not st:
        st = BotState(telegram_id=tg_id)
        db.add(st)
    st.flow = flow
    st.step = step
    st.data_json = json.dumps(data or {})
    db.commit()


def _clear_state(db: Session, tg_id: int) -> None:
    st = _get_state(db, tg_id)
    if st:
        st.flow = None
        st.step = None
        st.data_json = None
        db.commit()


def _state_data(st: BotState | None) -> dict:
    if not st or not st.data_json:
        return {}
    try:
        return json.loads(st.data_json)
    except json.JSONDecodeError:
        return {}


def _ensure_user(db: Session, tg_id: int, username: str | None) -> User:
    user = db.query(User).filter(User.telegram_id == tg_id).first()
    if not user:
        user = User(telegram_id=tg_id, username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
    elif username and user.username != username:
        user.username = username
        db.commit()
    return user


# ----------------------------- UI -----------------------------
def _main_menu() -> list:
    return [
        [{"text": "🛒 Place Order", "callback_data": "menu_order"}],
        [{"text": "💰 Wallet", "callback_data": "menu_wallet"}, {"text": "➕ Add Money", "callback_data": "menu_addmoney"}],
        [{"text": "🎁 Daily Reward", "callback_data": "menu_reward"}, {"text": "👥 Referral", "callback_data": "menu_referral"}],
        [{"text": "🎟 Support", "callback_data": "menu_ticket"}],
    ]


def _welcome() -> str:
    return (
        f"<b>Welcome to {settings.app_name}</b> 🚀\n\n"
        "Fast, secure and reliable social media growth services.\n"
        f"Support: @{settings.telegram_support_username}\n\n"
        "Use the menu below to get started."
    )


# ----------------------------- Flows -----------------------------
async def _show_wallet(db: Session, chat_id: int, tg_id: int) -> None:
    user = _ensure_user(db, tg_id, None)
    bal = wallet_balance(db, user.id)
    await send_message(chat_id, f"💰 <b>Wallet Balance:</b> ₹{bal:.2f}", keyboard=_main_menu())


async def _start_addmoney(db: Session, chat_id: int, tg_id: int) -> None:
    _set_state(db, tg_id, "addmoney", "amount", {})
    await send_message(
        chat_id,
        f"➕ <b>Add Money</b>\n\nEnter the amount in INR you want to add "
        f"(min ₹{settings.min_add_money_inr}, max ₹{settings.max_add_money_inr}).",
    )


async def _process_addmoney_amount(db: Session, chat_id: int, tg_id: int, text: str) -> None:
    try:
        amount = Decimal(text.strip())
    except (InvalidOperation, ValueError):
        await send_message(chat_id, "Please send a valid number, e.g. 200")
        return
    if amount < Decimal(str(settings.min_add_money_inr)) or amount > Decimal(str(settings.max_add_money_inr)):
        await send_message(
            chat_id,
            f"Amount must be between ₹{settings.min_add_money_inr} and ₹{settings.max_add_money_inr}.",
        )
        return

    _ensure_user(db, tg_id, None)

    # 1) Try Cashfree
    if cashfree_svc.is_configured():
        try:
            link = await cashfree_svc.create_payment_link(tg_id, amount)
            _clear_state(db, tg_id)
            await send_message(
                chat_id,
                f"💳 <b>Pay ₹{amount:.2f} via Cashfree</b>\n\nTap the secure link below. "
                "Your wallet is credited automatically after payment.",
                keyboard=[[{"text": "Pay Now ✅", "url": link["link_url"]}], [{"text": "« Menu", "callback_data": "menu_home"}]],
            )
            return
        except cashfree_svc.CashfreeError as exc:
            logger.warning("Cashfree failed, falling back to UPI: %s", exc)

    # 2) UPI fallback
    if not settings.upi_fallback_enabled or not settings.admin_upi_id:
        _clear_state(db, tg_id)
        await send_message(chat_id, "Payments are temporarily unavailable. Please contact support.", keyboard=_main_menu())
        return
    try:
        topup, uri, _ = upi_fallback.create_upi_topup(db, tg_id, amount)
    except upi_fallback.UpiError as exc:
        await send_message(chat_id, f"Could not start UPI payment: {exc}")
        return

    png = upi_fallback.generate_qr_png_bytes(uri)
    caption = (
        f"📲 <b>Pay ₹{amount:.2f} via UPI</b>\n\n"
        f"UPI ID: <code>{topup.upi_id}</code>\n"
        f"Reference: <code>{topup.reference}</code>\n\n"
        "Scan the QR (or use the UPI ID) in any UPI app. After paying, send me the "
        "<b>UTR / reference number</b> from your payment to credit your wallet."
    )
    await send_photo_bytes(chat_id, png, caption=caption)
    _set_state(db, tg_id, "addmoney", "utr", {"reference": topup.reference})


async def _process_utr(db: Session, chat_id: int, tg_id: int, text: str, reference: str) -> None:
    try:
        topup, status = upi_fallback.submit_utr(db, reference, text)
    except upi_fallback.UpiError as exc:
        await send_message(chat_id, str(exc))
        return
    if status == "credited":
        _clear_state(db, tg_id)
        user = _ensure_user(db, tg_id, None)
        bal = wallet_balance(db, user.id)
        await send_message(
            chat_id,
            f"✅ <b>Payment received!</b>\nWallet credited with ₹{topup.amount:.2f}.\n"
            f"New balance: ₹{bal:.2f}",
            keyboard=_main_menu(),
        )
    elif status == "pending_review":
        _clear_state(db, tg_id)
        await send_message(
            chat_id,
            "⏳ Your payment is being verified by our team and will be credited shortly. "
            f"Reference: <code>{reference}</code>",
            keyboard=_main_menu(),
        )
    elif status == "duplicate_utr":
        await send_message(chat_id, "⚠️ This UTR has already been used. Please send the correct UTR for this payment.")
    elif status == "already_done":
        _clear_state(db, tg_id)
        await send_message(chat_id, "This top-up is already processed.", keyboard=_main_menu())
    else:
        await send_message(chat_id, "Could not find this payment. Please start Add Money again.", keyboard=_main_menu())


async def _start_order(db: Session, chat_id: int, tg_id: int) -> None:
    _set_state(db, tg_id, "order", "platform", {})
    await send_message(chat_id, "🛒 <b>Place Order</b>\n\nSend the platform name (Instagram / YouTube / Telegram / Facebook):")


async def _order_platform(db: Session, chat_id: int, tg_id: int, text: str) -> None:
    services = (
        db.query(ServiceCatalog)
        .filter(ServiceCatalog.platform.ilike(text.strip()), ServiceCatalog.enabled.is_(True))
        .limit(15)
        .all()
    )
    if not services:
        await send_message(chat_id, "No services found for that platform. Try the exact name e.g. Instagram.")
        return
    lines = "\n".join([f"<code>{s.id}</code> — {s.service_name} (₹{s.base_rate}/unit)" for s in services])
    _set_state(db, tg_id, "order", "service", {"platform": text.strip()})
    await send_message(chat_id, f"Select a service by sending its ID:\n\n{lines}")


async def _order_service(db: Session, chat_id: int, tg_id: int, text: str, data: dict) -> None:
    if not text.strip().isdigit():
        await send_message(chat_id, "Please send a valid numeric service ID.")
        return
    service = db.query(ServiceCatalog).filter(ServiceCatalog.id == int(text.strip()), ServiceCatalog.enabled.is_(True)).first()
    if not service:
        await send_message(chat_id, "Service not found. Send a valid ID from the list.")
        return
    data["service_id"] = service.id
    _set_state(db, tg_id, "order", "link", data)
    await send_message(chat_id, f"Selected: {service.service_name}\n\nNow send the target <b>link</b>:")


async def _order_link(db: Session, chat_id: int, tg_id: int, text: str, data: dict) -> None:
    data["link"] = text.strip()
    _set_state(db, tg_id, "order", "qty", data)
    await send_message(chat_id, "Now send the <b>quantity</b>:")


async def _order_qty(db: Session, chat_id: int, tg_id: int, text: str, data: dict) -> None:
    if not text.strip().isdigit():
        await send_message(chat_id, "Quantity must be a number.")
        return
    qty = int(text.strip())
    service = db.query(ServiceCatalog).filter(ServiceCatalog.id == data.get("service_id")).first()
    if not service:
        _clear_state(db, tg_id)
        await send_message(chat_id, "Service no longer available.", keyboard=_main_menu())
        return
    if qty < service.min_qty or qty > service.max_qty:
        await send_message(chat_id, f"Quantity must be between {service.min_qty} and {service.max_qty}.")
        return

    user = _ensure_user(db, tg_id, None)
    rate = Decimal(str(service.sell_rate if service.sell_rate is not None else service.base_rate))
    charge = (rate * Decimal(qty) / Decimal("1000")).quantize(Decimal("0.01")) if rate < 1 else (rate * Decimal(qty)).quantize(Decimal("0.01"))
    bal = wallet_balance(db, user.id)
    if bal < charge:
        _clear_state(db, tg_id)
        await send_message(
            chat_id,
            f"❌ Insufficient balance.\nOrder cost: ₹{charge:.2f}\nYour balance: ₹{bal:.2f}\n\nPlease add money first.",
            keyboard=_main_menu(),
        )
        return

    # Place via provider engine
    from app.services.order_engine import place_order
    from app.services.wallet import add_ledger_entry

    result = await place_order(service.id, data.get("link", ""), qty, base_rate=float(service.base_rate))
    if result.get("status") == "created":
        order = Order(
            client_order_id=result["order_id"],
            user_id=user.id,
            provider_name=result["provider"],
            provider_order_id=result.get("provider_order_id"),
            service_id=service.id,
            link=data.get("link", ""),
            quantity=qty,
            charge_amount=charge,
            status="created",
        )
        db.add(order)
        add_ledger_entry(db, user.id, "debit", charge, reference_id=result["order_id"], note="Order")
        db.commit()
        _clear_state(db, tg_id)
        await send_message(
            chat_id,
            f"✅ <b>Order placed!</b>\nOrder ID: <code>{result['order_id']}</code>\n"
            f"Provider: {result['provider']}\nCharged: ₹{charge:.2f}",
            keyboard=_main_menu(),
        )
    else:
        _clear_state(db, tg_id)
        await send_message(
            chat_id,
            "⚠️ Could not place the order with providers right now. You were not charged. Please try again later.",
            keyboard=_main_menu(),
        )


async def _start_ticket(db: Session, chat_id: int, tg_id: int) -> None:
    _set_state(db, tg_id, "ticket", "subject", {})
    await send_message(chat_id, "🎟 <b>Support Ticket</b>\n\nSend the subject of your issue:")


async def _ticket_subject(db: Session, chat_id: int, tg_id: int, text: str) -> None:
    _set_state(db, tg_id, "ticket", "message", {"subject": text.strip()})
    await send_message(chat_id, "Now describe your issue:")


async def _ticket_message(db: Session, chat_id: int, tg_id: int, text: str, data: dict) -> None:
    _ensure_user(db, tg_id, None)
    ticket = create_ticket(db, tg_id, data.get("subject", "Support"), text.strip())
    _clear_state(db, tg_id)
    await send_message(
        chat_id,
        f"✅ Ticket created: <code>{ticket.ticket_ref}</code>\nOur team will respond soon. "
        f"You can also reach @{settings.telegram_support_username}.",
        keyboard=_main_menu(),
    )


# ----------------------------- Dispatcher -----------------------------
async def handle_update(update: dict, db: Session) -> None:
    if "callback_query" in update:
        await _handle_callback(update["callback_query"], db)
        return
    message = update.get("message") or update.get("edited_message")
    if not message:
        return
    await _handle_message(message, db)


async def _handle_callback(cq: dict, db: Session) -> None:
    data = cq.get("data", "")
    chat_id = cq["message"]["chat"]["id"]
    tg_id = cq["from"]["id"]
    username = cq["from"].get("username")
    _ensure_user(db, tg_id, username)
    await answer_callback(cq.get("id", ""))

    if data in ("menu_home",):
        _clear_state(db, tg_id)
        await send_message(chat_id, "Main Menu", keyboard=_main_menu())
    elif data == "menu_wallet":
        await _show_wallet(db, chat_id, tg_id)
    elif data == "menu_addmoney":
        await _start_addmoney(db, chat_id, tg_id)
    elif data == "menu_order":
        await _start_order(db, chat_id, tg_id)
    elif data == "menu_ticket":
        await _start_ticket(db, chat_id, tg_id)
    elif data == "menu_reward":
        status = credit_daily_reward(db, tg_id)
        msg = {"claimed": "🎁 Daily reward credited!", "already_claimed": "You already claimed today's reward."}.get(status, status)
        await send_message(chat_id, msg, keyboard=_main_menu())
    elif data == "menu_referral":
        await send_message(
            chat_id,
            f"👥 <b>Referral</b>\n\nShare your link:\nhttps://t.me/{settings.telegram_bot_username}?start=ref_{tg_id}\n\n"
            "You earn a reward whenever someone you referred adds money.",
            keyboard=_main_menu(),
        )


async def _handle_message(message: dict, db: Session) -> None:
    chat_id = message["chat"]["id"]
    frm = message.get("from", {})
    tg_id = frm.get("id")
    username = frm.get("username")
    text = message.get("text", "") or ""
    if tg_id is None:
        return
    _ensure_user(db, tg_id, username)

    # Commands
    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].startswith("ref_"):
            try:
                referrer = int(parts[1][4:])
                register_referral(db, referrer, tg_id)
            except (ValueError, Exception):  # noqa: BLE001
                pass
        _clear_state(db, tg_id)
        await send_message(chat_id, _welcome(), keyboard=_main_menu())
        return
    if text.startswith("/menu"):
        _clear_state(db, tg_id)
        await send_message(chat_id, "Main Menu", keyboard=_main_menu())
        return
    if text.startswith("/wallet") or text.startswith("/balance"):
        await _show_wallet(db, chat_id, tg_id)
        return
    if text.startswith("/addmoney"):
        await _start_addmoney(db, chat_id, tg_id)
        return
    if text.startswith("/support"):
        await send_message(chat_id, f"Contact support: @{settings.telegram_support_username}", keyboard=_main_menu())
        return

    # Stateful flows
    st = _get_state(db, tg_id)
    if st and st.flow:
        data = _state_data(st)
        if st.flow == "addmoney" and st.step == "amount":
            await _process_addmoney_amount(db, chat_id, tg_id, text)
        elif st.flow == "addmoney" and st.step == "utr":
            await _process_utr(db, chat_id, tg_id, text, data.get("reference", ""))
        elif st.flow == "order" and st.step == "platform":
            await _order_platform(db, chat_id, tg_id, text)
        elif st.flow == "order" and st.step == "service":
            await _order_service(db, chat_id, tg_id, text, data)
        elif st.flow == "order" and st.step == "link":
            await _order_link(db, chat_id, tg_id, text, data)
        elif st.flow == "order" and st.step == "qty":
            await _order_qty(db, chat_id, tg_id, text, data)
        elif st.flow == "ticket" and st.step == "subject":
            await _ticket_subject(db, chat_id, tg_id, text)
        elif st.flow == "ticket" and st.step == "message":
            await _ticket_message(db, chat_id, tg_id, text, data)
        return

    # Default
    await send_message(chat_id, "Use the menu below 👇", keyboard=_main_menu())
