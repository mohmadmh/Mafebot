from flask import Flask, request
import asyncio
from telegram import Update
from telegram.ext import Application

app = Flask(__name__)

TOKEN = "8572686550:AAGzwx3rmEMXrSXAySuD8oUgU1G2LnKmKQM"
# إنشاء التطبيق
application = Application.builder().token(TOKEN).build()

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        try:
            update = Update.de_json(request.get_json(force=True), application.bot)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # تشغيل معالجة الرسالة
            loop.run_until_complete(application.initialize())
            loop.run_until_complete(application.process_update(update))
            return "OK"
        except Exception as e:
            return f"Error: {str(e)}", 200 # نرسل 200 لنرى الخطأ في الصفحة
    return "<h1>البوت يعمل يا @H0_Om!</h1><p>الآن اضغط على رابط تفعيل Webhook.</p>"

# للمحاكاة المحلية فقط
if __name__ == "__main__":
    app.run(debug=True)
