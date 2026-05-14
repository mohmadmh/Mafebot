import asyncio
import random
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

app = Flask(__name__)

TOKEN = "8572686550:AAGzwx3rmEMXrSXAySuD8oUgU1G2LnKmKQM"
DEV_USER = "H0_Om"

application = Application.builder().token(TOKEN).build()
players = {} # لتخزين اللاعبين المنضمين

async def start(update: Update, context):
    user = update.effective_user
    text = f"🕵️ أهلاً بك يا {user.first_name} في لعبة المافيا!"
    if user.username == DEV_USER:
        text += "\n\n🛠 **أهلاً بالمطور @H0_Om، البوت تحت سيطرتك.**"
    
    keyboard = [[InlineKeyboardButton("انضمام للعبة ✅", callback_data="join")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context):
    query = update.callback_query
    user = query.from_user
    
    if query.data == "join":
        if user.id not in players:
            players[user.id] = user.first_name
            await query.message.reply_text(f"👤 انضم اللاعب: {user.first_name}")
            
            # لوحة تحكم المطور تظهر لك فقط عند انضمام أول لاعب
            if user.username == DEV_USER:
                dev_keyboard = [[InlineKeyboardButton("🎲 توزيع الأدوار", callback_data="deal")]]
                await query.message.reply_text("🛠 لوحة تحكم المطور:", reply_markup=InlineKeyboardMarkup(dev_keyboard))
        await query.answer()

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        try:
            update_data = request.get_json(force=True)
            update = Update.de_json(update_data, application.bot)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if not application.handlers:
                application.add_handler(CommandHandler("start", start))
                application.add_handler(CallbackQueryHandler(handle_callback))
            
            loop.run_until_complete(application.initialize())
            loop.run_until_complete(application.process_update(update))
            return "OK", 200
        except Exception as e:
            return str(e), 200
    return "<h1>البوت مستعد يا @H0_Om</h1>"
