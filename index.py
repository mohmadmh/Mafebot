import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler

app = Flask(__name__)

# بياناتك كمطور
TOKEN = "8572686550:AAGzwx3rmEMXrSXAySuD8oUgU1G2LnKmKQM"

# إعداد التطبيق
application = Application.builder().token(TOKEN).build()

async def start(update, context):
    await update.message.reply_text("✅ أهلاً مطور @H0_Om! البوت يعمل الآن بنجاح.")

# تسجيل الأوامر
application.add_handler(CommandHandler("start", start))

@app.route('/', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        try:
            update = Update.de_json(request.get_json(force=True), application.bot)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(application.initialize())
            loop.run_until_complete(application.process_update(update))
            return "OK", 200
        except Exception as e:
            return str(e), 500
    return "Mafia Bot is Online for @H0_Om", 200
