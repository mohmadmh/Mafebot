import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

app = Flask(__name__)

TOKEN = "8572686550:AAGzwx3rmEMXrSXAySuD8oUgU1G2LnKmKQM"

# إعداد التطبيق بدون تعقيدات
application = Application.builder().token(TOKEN).build()

async def echo_all(update: Update, context):
    # سيرد البوت على أي رسالة تصل إليه بهذا النص
    await update.message.reply_text(f"✅ وصلت رسالتك يا {update.effective_user.first_name}! أنا أعمل الآن.")

# إضافة معالج لكل الرسائل النصية
application.add_handler(MessageHandler(filters.TEXT, echo_all))

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        try:
            update_data = request.get_json(force=True)
            update = Update.de_json(update_data, application.bot)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            loop.run_until_complete(application.initialize())
            loop.run_until_complete(application.process_update(update))
            return "OK", 200
        except Exception as e:
            # إذا حدث خطأ أثناء المعالجة سيظهر هنا
            print(f"Error logic: {e}")
            return str(e), 200
            
    return "<h1>البوت يعمل يا @H0_Om!</h1>"
