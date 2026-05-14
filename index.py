import os
import random
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

app = Flask(__name__)

# بيانات البوت والمطور
TOKEN = "8572686550:AAGzwx3rmEMXrSXAySuD8oUgU1G2LnKmKQM"
DEVELOPER_USERNAME = "H0_Om" # المطور الفعلي @H0_Om

# بناء التطبيق بنظام الـ Webhook
application = Application.builder().token(TOKEN).build()

# تخزين بيانات اللعبة (ملاحظة: الذاكرة مؤقتة في Vercel)
game_state = {
    "players": {}, # {user_id: {"name": name, "role": role}}
    "votes": {},   # {target_id: count}
    "voted_users": [],
    "is_active": False
}

def is_dev(user):
    return user.username == DEVELOPER_USERNAME

# --- الأوامر الأساسية ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome = f"أهلاً بك يا {user.first_name} في بوت المافيا المطور! 🕵️‍♂️"
    if is_dev(user):
        welcome += "\n\n🛠 **تم التعرف عليك كمطور للبوت.**"
    
    await update.message.reply_text(
        welcome,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("بدء لعبة جديدة 🎮", callback_data="new_game")]
        ])
    )

# --- معالجة الأزرار ---

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    data = query.data

    # 1. بدء لعبة جديدة (للمطور فقط أو للجميع حسب رغبتك)
    if data == "new_game":
        game_state["players"].clear()
        game_state["is_active"] = True
        await query.edit_message_text(
            "🎮 **بدأت جولة جديدة!**\nاضغط على الزر أدناه للانضمام.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("انضمام ✅", callback_data="join")]
            ])
        )

    # 2. انضمام اللاعبين
    elif data == "join":
        if user.id not in game_state["players"]:
            game_state["players"][user.id] = {"name": user.first_name, "role": None}
            await query.message.reply_text(f"✅ انضم اللاعب: {user.first_name}")
            
            # إذا كان المطور هو من انضم، نعطيه زر التوزيع
            if is_dev(user) and len(game_state["players"]) >= 1:
                await query.message.reply_text(
                    "🛠 **لوحة تحكم المطور:**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("توزيع الأدوار 🎲", callback_data="distribute")]
                    ])
                )
        await query.answer()

    # 3. توزيع الأدوار (للمطور @H0_Om فقط)
    elif data == "distribute":
        if not is_dev(user):
            await query.answer("هذا الزر للمطور فقط! 🚫", show_alert=True)
            return

        uids = list(game_state["players"].keys())
        if len(uids) < 3:
            await query.answer("نحتاج 3 لاعبين على الأقل!", show_alert=True)
            return

        roles = ["مافيا 🔪", "طبيب 💊", "محقق 🔍"] + ["مواطن 👨‍🌾"] * (len(uids) - 3)
        random.shuffle(roles)

        for i, uid in enumerate(uids):
            game_state["players"][uid]["role"] = roles[i]
            try:
                await context.bot.send_message(chat_id=uid, text=f"🕵️ دورك السري: {roles[i]}")
            except:
                pass # في حال لم يبدأ اللاعب محادثة مع البوت

        await query.edit_message_text(
            "✅ تم توزيع الأدوار سراً!\nبدأ وقت النقاش..",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("بدء التصويت 🗳️", callback_data="start_vote")]
            ])
        )

    # 4. بدء التصويت
    elif data == "start_vote":
        keyboard = []
        for uid, info in game_state["players"].items():
            keyboard.append([InlineKeyboardButton(f"إقصاء {info['name']}", callback_data=f"v_{uid}")])
        
        game_state["votes"].clear()
        game_state["voted_users"].clear()
        await query.edit_message_text("🗳️ **وقت التصويت!**\nاختر من تريد إقصاءه:", reply_markup=InlineKeyboardMarkup(keyboard))

    # 5. تسجيل الصوت
    elif data.startswith("v_"):
        target_id = int(data.split("_")[1])
        if user.id in game_state["voted_users"]:
            await query.answer("صوتك مسجل مسبقاً! ⚠️", show_alert=True)
            return

        game_state["votes"][target_id] = game_state["votes"].get(target_id, 0) + 1
        game_state["voted_users"].append(user.id)
        await query.answer(f"تم التصويت ضد {game_state['players'][target_id]['name']}")

        if len(game_state["voted_users"]) >= len(game_state["players"]):
            voted_out = max(game_state["votes"], key=game_state["votes"].get)
            name = game_state["players"][voted_out]["name"]
            await query.message.reply_text(f"💀 تم إقصاء **{name}** من اللعبة!")
            del game_state["players"][voted_out]

# --- إعدادات Flask لـ Vercel ---

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler))

@app.route('/', methods=['POST', 'GET'])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.initialize()
        await application.process_update(update)
        return "ok", 200
    return "البوت يعمل بنجاح! @H0_Om", 200
