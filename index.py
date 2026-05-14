import asyncio
import random
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

app = Flask(__name__)

TOKEN = "8572686550:AAGzwx3rmEMXrSXAySuD8oUgU1G2LnKmKQM"

# مخزن بيانات اللعبة
game_data = {
    "players": {},      # {user_id: {"name": name, "role": None}}
    "creator_id": None, # معرف الشخص الذي بدأ اللعبة
    "is_started": False
}

application = Application.builder().token(TOKEN).build()

async def start(update: Update, context):
    user = update.effective_user
    # بمجرد كتابة /start، الشخص الذي ضغط هو المرشح ليكون المنشئ
    game_data["creator_id"] = user.id
    game_data["players"] = {}
    game_data["is_started"] = False
    
    text = f"🕵️ جولة مافيا جديدة!\nالمنشئ: {user.first_name}\n\nاضغط انضمام للمشاركة."
    keyboard = [[InlineKeyboardButton("انضمام للعبة ✅", callback_data="join")]]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context):
    query = update.callback_query
    user = query.from_user
    data = query.data

    # 1. الانضمام (متاح للجميع)
    if data == "join":
        if game_data["is_started"]:
            await query.answer("عذراً، اللعبة بدأت بالفعل! ⏳", show_alert=True)
            return

        if user.id not in game_data["players"]:
            game_data["players"][user.id] = {"name": user.first_name}
            await query.message.reply_text(f"👤 انضم اللاعب: {user.first_name}")
            
            # إظهار أزرار التحكم فقط لمن بدأ اللعبة (Creator)
            if user.id == game_data["creator_id"]:
                control_keyboard = [
                    [InlineKeyboardButton("🚀 ابدأ اللعبة", callback_data="run_game")],
                    [InlineKeyboardButton("🔄 رسترة (إعادة تعيين)", callback_data="reset_game")]
                ]
                await query.message.reply_text(
                    "🛠 **لوحة تحكم المنشئ:**",
                    reply_markup=InlineKeyboardMarkup(control_keyboard)
                )
        await query.answer()

    # 2. بدء اللعب (خاص بالمنشئ فقط)
    elif data == "run_game":
        if user.id != game_data["creator_id"]:
            await query.answer("هذا الزر خاص بمنشئ اللعبة فقط! 🚫", show_alert=True)
            return

        if len(game_data["players"]) < 3:
            await query.answer("نحتاج 3 لاعبين على الأقل! 👥", show_alert=True)
            return

        game_data["is_started"] = True
        uids = list(game_data["players"].keys())
        roles = ["مافيا 🔪", "طبيب 💊", "محقق 🔍"] + ["مواطن 👨‍🌾"] * (len(uids) - 3)
        random.shuffle(roles)

        for i, uid in enumerate(uids):
            role = roles[i]
            try:
                await context.bot.send_message(chat_id=uid, text=f"🕵️ دورك السري: {role}")
            except: pass

        await query.edit_message_text("✅ تم توزيع الأدوار سراً! انطلقوا للنقاش.")

    # 3. الرسترة (خاص بالمنشئ فقط)
    elif data == "reset_game":
        if user.id != game_data["creator_id"]:
            await query.answer("المنشئ فقط يمكنه إعادة التعيين! 🔄", show_alert=True)
            return

        game_data["players"] = {}
        game_data["is_started"] = False
        await query.edit_message_text("🔄 تم رسترة اللعبة بنجاح. يمكنكم الانضمام من جديد.")
        await query.answer("تمت الرسترة")

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
    return "<h1>البوت يعمل بنظام التحكم للمنشئ يا @H0_Om</h1>"
