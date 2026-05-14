import os
import random
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

app = Flask(__name__)

# بيانات البوت والمطور
TOKEN = "8572686550:AAGzwx3rmEMXrSXAySuD8oUgU1G2LnKmKQM"
DEVELOPER_USERNAME = "H0_Om"  # يوزرك المطور

application = Application.builder().token(TOKEN).build()
players_list = {}

# دالة للتحقق هل المستخدم هو المطور
def is_developer(user):
    return user.username == DEVELOPER_USERNAME

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players_list.clear()
    
    # رسالة الترحيب مع التحقق من المطور
    welcome_text = "🎮 **لعبة المافيا بدأت!**"
    if is_developer(update.effective_user):
        welcome_text += "\n\n⚠️ **أهلاً بالمطور! لديك صلاحيات التحكم الكامل.**"

    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("انضمام للعبة ✅", callback_data="join")]
        ])
    )

async def handle_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    
    if user.id not in players_list:
        players_list[user.id] = user.first_name
        await query.message.reply_text(f"👤 انضم اللاعب: {user.first_name}")

    # لوحة تحكم المطور (تظهر فقط لك)
    if is_developer(user) and len(players_list) >= 1: # جعلتها 1 للتجربة فقط
        await query.message.reply_text(
            "🛠 **لوحة تحكم المطور:**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎲 توزيع الأدوار الآن", callback_data="distribute")],
                [InlineKeyboardButton("❌ إنهاء اللعبة فوراً", callback_data="reset_game")]
            ])
        )
    await query.answer()

async def handle_dev_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    # التأكد أن من يضغط على أزرار التحكم هو المطور حصراً
    if not is_developer(user):
        await query.answer("عذراً، هذه الصلاحية للمطور @H0_Om فقط! 🚫", show_alert=True)
        return

    if query.data == "reset_game":
        players_list.clear()
        await query.edit_message_text("🔄 تم إنهاء اللعبة وتصفير القائمة بواسطة المطور.")
    
    elif query.data == "distribute":
        if len(players_list) < 2: # للتجربة وضعتها 2، في الحقيقة تحتاج أكثر
            await query.answer("نحتاج لاعبين أكثر للتوزيع!", show_alert=True)
            return
        
        # كود التوزيع (نفس السابق)
        await query.message.reply_text("⏳ جاري توزيع الأدوار سراً...")
        # ... (منطق التوزيع)
        await query.answer("تم التوزيع!")

# المعالجات
application.add_handler(CommandHandler("start", start_game))
application.add_handler(CallbackQueryHandler(handle_join, pattern="join"))
application.add_handler(CallbackQueryHandler(handle_dev_actions, pattern="^(distribute|reset_game)$"))

@app.route('/', methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.initialize()
    await application.process_update(update)
    return "ok", 200
