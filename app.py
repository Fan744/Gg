import os
import aiohttp
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("7746673219:AAGfbNsG3Ray0lnaLzXlQ-mXQUkESh7Jp5E")  # Set your bot token
API_URL = "https://prod.fitflexapp.com/api/users/signupV1"
COOLDOWN = 60  # seconds

# Track last request per user
last_request = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "FITFLEX OTP TESTER\n\n"
        "Send:\n"
        "`/phone 923001234567` → Test phone OTP\n"
        "`/email user@gmail.com` → Test email OTP\n\n"
        "1 request per 60 seconds only.",
        parse_mode="Markdown"
    )

async def send_otp(update: Update, context: ContextTypes.DEFAULT_TYPE, method: str):
    user_id = update.effective_user.id
    now = asyncio.get_event_loop().time()

    # Cooldown check
    if user_id in last_request and now - last_request[user_id] < COOLDOWN:
        wait = int(COOLDOWN - (now - last_request[user_id]))
        await update.message.reply_text(f"Please wait {wait} seconds.")
        return

    if not context.args:
        await update.message.reply_text(f"Usage: `/{method} <value>`", parse_mode="Markdown")
        return

    value = context.args[0].strip()

    # Basic validation
    if method == "phone" and not value.startswith("92") or len(value) != 12:
        await update.message.reply_text("Use Pakistani number: `923001234567`")
        return
    if method == "email" and "@" not in value:
        await update.message.reply_text("Invalid email.")
        return

    msg = await update.message.reply_text("Sending OTP...")

    payload = {
        "type": "msisdn" if method == "phone" else "email",
        "user_platform": "Android",
        "country_id": "162",
        "msisdn": value if method == "phone" else "",
        "email": value if method == "email" else ""
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, timeout=10) as resp:
                text = await resp.text()
                status = resp.status

        if status == 200:
            await msg.edit_text(f"OTP sent to {value}\nCheck your phone/email.")
        else:
            await msg.edit_text(f"Failed ({status})\nResponse: `{text[:100]}...`", parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"Error: {e}")

    last_request[user_id] = now

def main():
    if not BOT_TOKEN:
        print("Set BOT_TOKEN in environment!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("phone", lambda u, c: send_otp(u, c, "phone")))
    app.add_handler(CommandHandler("email", lambda u, c: send_otp(u, c, "email")))
    app.add_handler(MessageHandler(filters.COMMAND, start))  # fallback

    print("FITFLEX OTP Tester is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
