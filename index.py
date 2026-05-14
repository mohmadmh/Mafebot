import asyncio
import random
import time
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

app = Flask(__name__)

TOKEN = "8572686550:AAGzwx3rmEMXrSXAySuD8oUgU1G2LnKmKQM"

# إعدادات الأوقات (بالثواني)
DISCUSSION_TIME = 90
VOTING_TIME = 45

game_data = {
    "players": {},
    "creator_id": None,
    "is_started": False,
    "start_time": 0,
    "phase": None # "discussion" or "voting"
}

application = Application.builder().token(TOKEN).build()

async def start(update: Update, context):
    user = update.effective_user
    game_data["creator_id"] = user.id
    game_data["players"] = {}
    game_data["is_started"] = False
    game_data["phase"] = None
    
    text = f"🕵️ جولة مافيا جديدة!\nالمنشئ: {user.first_name}\n\nنظام الوقت:\n💬 نقاش: {DISCUSSION_TIME}ث\n🗳 تصويت: {VOTING_TIME}ث"
    keyboard = [[InlineKeyboardButton("انضمام للعبة ✅", callback_data="join")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context):
    query = update.callback_query
    user = query.from_user
    data = query.data

    if data == "join":
        if game_data["is_started"]:
            await query.answer("اللعبة بدأت! انتظر الجولة القادمة. ⏳", show_alert=True)
            return
        if user.id not in game_data["players"]:
            game_data["players"][user.id] = {"name": user.first_name}
            await query.message.reply_text(f"👤 انضم: {user.first_name}")
            if user.id == game_data["creator_id"]:
                keyboard = [
                    [InlineKeyboardButton("🚀 ابدأ الجولة", callback_data="run_game")],
                    [InlineKeyboardButton("🔄 رسترة", callback_data="reset_game")]
                ]
                await query.message.reply_text("🛠 لوحة المنشئ:", reply_markup=InlineKeyboardMarkup(keyboard))
        await query.answer()

    elif data == "run_game":
        if user.id != game_data["creator_id"]:
            await query.answer("للمنشئ فقط! 🚫", show_alert=True)
            return
        if len(game_data["players"]) < 3:
            await query.answer("نحتاج 3 لاعبين على الأقل! 👥", show_alert=True)
            return

        game_data["is_started"] = True
        game_data["phase"] = "discussion"
        
        # توزيع الأدوار
        uids = list(game_data["players"].keys())
        roles = ["مافيا 🔪", "طبيب 💊", "محقق 🔍"] + ["مواطن 👨‍🌾"] * (len(uids) - 3)
        random.shuffle(roles)
        for i, uid in enumerate(uids):
            try: await context.bot.send_message(chat_id=uid, text=f"🕵️ دورك السري: {roles[i]}")
            except: pass

        await query.edit_message_text(f"✅ بدأت الجولة!\n💬 **وقت النقاش:** {DISCUSSION_TIME} ثانية.\nتحدثوا الآن!")
        
        # مؤقت النقاش
        await asyncio.sleep(DISCUSSION_TIME)
        await start_voting_phase(query.message, context)

    elif data == "reset_game":
        if user.id == game_data["creator_id"]:
            game_data["players"] = {}
            game_data["is_started"] = False
            await query.edit_message_text("🔄 تم تصفير اللعبة.")
        await query.answer()

async def start_voting_phase(message, context):
    game_data["phase"] = "voting"
    keyboard = []
    for uid, info in game_data["players"].items():
        keyboard.append([InlineKeyboardButton(f"إقصاء {info['name']}", callback_data=f"vote_{uid}")])
    
    await message.reply_text(f"🗳 **انتهى النقاش!**\nبدأ وقت التصويت ({VOTING_TIME} ثانية).", reply_markup=InlineKeyboardMarkup(keyboard))
    
    # مؤقت التصويت
    await asyncio.sleep(VOTING_TIME)
    if game_data["phase"] == "voting":
        await message.reply_text("⌛ انتهى وقت التصويت!")
        game_data["phase"] = None

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
        except Exception as e: return str(e), 200
    return "<h1>Timer System Active for @H0_Om</h1>"
