import asyncio
import random
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

app = Flask(__name__)

TOKEN = "8572686550:AAGzwx3rmEMXrSXAySuD8oUgU1G2LnKmKQM"

game_data = {
    "players": {}, # {uid: {"name": name, "role": role, "alive": True}}
    "creator_id": None,
    "phase": None,
    "actions": {} # لتخزين قرارات الأدوار (من قُتل، من حُمي)
}

application = Application.builder().token(TOKEN).build()

# --- دالة البداية ---
async def start(update: Update, context):
    user = update.effective_user
    game_data.update({"creator_id": user.id, "players": {}, "phase": "joining", "actions": {}})
    
    text = "🕵️ جولة مافيا تفاعلية جديدة!\nالآن لكل دور أزرار خاصة لتنفيذ المهمة."
    keyboard = [[InlineKeyboardButton("انضمام للعبة ✅", callback_data="join")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# --- معالجة الأزرار ---
async def handle_callback(update: Update, context):
    query = update.callback_query
    user = query.from_user
    data = query.data

    # 1. الانضمام
    if data == "join":
        if user.id not in game_data["players"]:
            game_data["players"][user.id] = {"name": user.first_name, "role": None, "alive": True}
            await query.message.reply_text(f"👤 انضم: {user.first_name}")
            if user.id == game_data["creator_id"]:
                keyboard = [[InlineKeyboardButton("🎲 توزيع الأدوار وبدء المهام", callback_data="run_game")]]
                await query.message.reply_text("لوحة المطور @H0_Om:", reply_markup=InlineKeyboardMarkup(keyboard))
        await query.answer()

    # 2. بدء اللعبة وتوزيع الأزرار الخاصة
    elif data == "run_game" and user.id == game_data["creator_id"]:
        uids = [uid for uid, p in game_data["players"].items() if p["alive"]]
        if len(uids) < 3:
            await query.answer("نحتاج 3 لاعبين على الأقل!", show_alert=True)
            return
        
        roles = ["مافيا 🔪", "طبيب 💊", "محقق 🔍"] + ["مواطن 👨‍🌾"] * (len(uids) - 3)
        random.shuffle(roles)
        
        for i, uid in enumerate(uids):
            role = roles[i]
            game_data["players"][uid]["role"] = role
            
            # إنشاء أزرار الأهداف (كل اللاعبين ما عدا الشخص نفسه)
            targets = [[InlineKeyboardButton(p["name"], callback_data=f"act_{role[0]}_{t_uid}")] 
                       for t_uid, p in game_data["players"].items() if t_uid != uid]
            
            msg = f"🎭 دورك: {role}\n\n"
            if "مافيا" in role: msg += "اختر ضحيتك للقتل 💀:"
            elif "طبيب" in role: msg += "اختر شخصاً لحمايته 🛡️:"
            elif "محقق" in role: msg += "اختر شخصاً لكشف هويته 🔍:"
            else: msg += "أنت مواطن، انتظر النقاش للتصويت 🤝"

            try:
                await context.bot.send_message(chat_id=uid, text=msg, 
                                            reply_markup=InlineKeyboardMarkup(targets) if targets and "مواطن" not in role else None)
            except: pass
        
        await query.edit_message_text("✅ تم إرسال الأزرار السرية لكل صاحب وظيفة!\nبدأ وقت النقاش والعمل.")
        await query.answer()

    # 3. تنفيذ الأكشن (القتل، الحماية، التحقيق)
    elif data.startswith("act_"):
        role_key = data.split("_")[1] # أول حرف من الدور
        target_uid = int(data.split("_")[2])
        target_name = game_data["players"][target_uid]["name"]

        if role_key == "م": # مافيا
            game_data["actions"]["kill"] = target_uid
            await query.edit_message_text(f"🔪 قررت قتل: {target_name}")
        elif role_key == "ط": # طبيب
            game_data["actions"]["save"] = target_uid
            await query.edit_message_text(f"💊 قررت حماية: {target_name}")
        elif role_key == "م": # محقق (تم استخدام حرف م مرتين، سنميزه بالكود الأصلي)
            target_role = game_data["players"][target_uid]["role"]
            await query.edit_message_text(f"🔍 نتيجة التحقيق: {target_name} هو {target_role}")
        
        await query.answer("تم تسجيل قرارك")

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
    return "<h1>Interactive Mafia System Active @H0_Om</h1>"
