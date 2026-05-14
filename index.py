import asyncio
import random
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

app = Flask(__name__)

TOKEN = "8572686550:AAGzwx3rmEMXrSXAySuD8oUgU1G2LnKmKQM"

# إعدادات الأوقات الجديدة (مقللة حسب طلبك)
DISCUSSION_TIME = 45 
VOTING_TIME = 30
EXTEND_TIME = 30

game_data = {
    "players": {},
    "creator_id": None,
    "is_started": False,
    "phase": None,
    "timer_task": None # للتحكم في إلغاء أو تمديد الوقت
}

application = Application.builder().token(TOKEN).build()

async def start(update: Update, context):
    user = update.effective_user
    game_data.update({"creator_id": user.id, "players": {}, "is_started": False, "phase": None})
    
    text = f"🕵️ جولة مافيا سريعة!\nالمنشئ: {user.first_name}\n\n⏱ النقاش: {DISCUSSION_TIME}ث | التصويت: {VOTING_TIME}ث"
    keyboard = [[InlineKeyboardButton("انضمام ✅", callback_data="join")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context):
    query = update.callback_query
    user = query.from_user
    data = query.data

    if data == "join":
        if not game_data["is_started"] and user.id not in game_data["players"]:
            game_data["players"][user.id] = {"name": user.first_name}
            await query.message.reply_text(f"👤 انضم: {user.first_name}")
            if user.id == game_data["creator_id"]:
                keyboard = [[InlineKeyboardButton("🚀 ابدأ اللعبة", callback_data="run_game")]]
                await query.message.reply_text("لوحة المنشئ:", reply_markup=InlineKeyboardMarkup(keyboard))
        await query.answer()

    elif data == "run_game" and user.id == game_data["creator_id"]:
        if len(game_data["players"]) < 3:
            await query.answer("نحتاج 3 لاعبين على الأقل! 👥", show_alert=True)
            return
        
        game_data["is_started"] = True
        uids = list(game_data["players"].keys())
        
        # ضمان وجود مافيا واحد على الأقل
        roles = ["مافيا 🔪", "طبيب 💊", "محقق 🔍"] + ["مواطن 👨‍🌾"] * (len(uids) - 3)
        random.shuffle(roles)
        
        for i, uid in enumerate(uids):
            game_data["players"][uid]["role"] = roles[i]
            try: await context.bot.send_message(chat_id=uid, text=f"🕵️ دورك السري: {roles[i]}")
            except: pass

        await start_discussion(query.message, context)

    elif data == "extend_time" and user.id == game_data["creator_id"]:
        await query.message.reply_text(f"➕ تم تمديد وقت النقاش {EXTEND_TIME} ثانية بواسطة المنشئ.")
        await asyncio.sleep(EXTEND_TIME) # تمديد بسيط
        await query.answer()

    elif data == "skip_phase" and user.id == game_data["creator_id"]:
        if game_data["phase"] == "discussion":
            await start_voting(query.message, context)
        await query.answer("تم تخطي المرحلة.")

    elif data == "end_round" and user.id == game_data["creator_id"]:
        game_data["is_started"] = False
        await query.message.reply_text("🛑 تم إنهاء الجولة بواسطة المنشئ.")
        await query.answer()

async def start_discussion(message, context):
    game_data["phase"] = "discussion"
    keyboard = [
        [InlineKeyboardButton("⏩ تخطي النقاش (سكب)", callback_data="skip_phase")],
        [InlineKeyboardButton("➕ تمديد الوقت", callback_data="extend_time")],
        [InlineKeyboardButton("🛑 إنهاء الجولة", callback_data="end_round")]
    ]
    await message.reply_text(f"📢 **بدأ وقت النقاش!**\nلديك {DISCUSSION_TIME} ثانية لتحديد المافيا.. تحدثوا!", 
                            reply_markup=InlineKeyboardMarkup(keyboard))
    
    await asyncio.sleep(DISCUSSION_TIME)
    if game_data["phase"] == "discussion":
        await start_voting(message, context)

async def start_voting(message, context):
    game_data["phase"] = "voting"
    keyboard = []
    for uid, info in game_data["players"].items():
        keyboard.append([InlineKeyboardButton(f"إقصاء {info['name']}", callback_data=f"v_{uid}")])
    
    await message.reply_text(f"🗳 **بدأ وقت التصويت!** ({VOTING_TIME} ثانية)", reply_markup=InlineKeyboardMarkup(keyboard))
    await asyncio.sleep(VOTING_TIME)
    if game_data["phase"] == "voting":
        await message.reply_text("⌛ انتهى الوقت! سيتم تحليل النتائج..")
        game_data["is_started"] = False

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        try:
            update = Update.de_json(request.get_json(force=True), application.bot)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            if not application.handlers:
                application.add_handler(CommandHandler("start", start))
                application.add_handler(CallbackQueryHandler(handle_callback))
            loop.run_until_complete(application.initialize())
            loop.run_until_complete(application.process_update(update))
            return "OK", 200
        except Exception as e: return str(e), 200
    return "<h1>Mafia Game System Active @H0_Om</h1>"
