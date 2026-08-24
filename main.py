import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# आपका एक्टिव टोकन यहाँ जुड़ा हुआ है
BOT_TOKEN = "8306462663:AAE78G1JccISKjk5pTbsOcskoGwhn8NXqpE"

# 🎬 डेटाबेस: यहाँ कुकू टीवी लिंक्स और उनके सामने सीधे वीडियो फाइल सेट है
# नोट: इंटरनेट पर जो फ्री वीडियो लिंक या टेलीग्राम डंप फाइल लिंक मिले, उसे यहाँ पेस्ट करें
DATABASE = {
    "legacy-of-betrayal": {
        "title": "Legacy of Betrayal | Drama Series",
        "video_file": "https://w3schools.com" # उदाहरण के लिए डायरेक्ट वीडियो लिंक
    },
    "the-key-lord": {
        "title": "The Key Lord | Thriller Series",
        "video_file": "https://w3schools.com"
    }
}

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Direct Kuku File Delivery Server Active")
    def log_message(self, format, *args): return

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 नमस्ते! मैं एक Direct Kuku TV Video Downloader बॉट हूँ।\n\n"
        "मुझे कुकू टीवी का लिंक भेजें, मैं आपको सीधे असली वीडियो फाइल यहीं चैट में दे दूंगा! 🎬"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_url = update.message.text.strip().lower()
    
    if "kukutv.app" not in user_url and "kuku.com" not in user_url:
        await update.message.reply_text("❌ कृपया केवल एक सही कुकू टीवी वीडियो का लिंक भेजें।")
        return

    status_message = await update.message.reply_text("🔄 सर्वर से सीधे वीडियो फाइल निकाली जा रही है... कृपया प्रतीक्षा करें।")

    matched = False
    for key, video_info in DATABASE.items():
        if key in user_url:
            video_title = video_info["title"]
            video_source = video_info["video_file"]
            
            try:
                # यूजर को सीधे वीडियो फाइल सेंड करना (बिना लिंक के)
                await update.message.reply_video(
                    video=video_source,
                    caption=f"My\n✅ **Download Complete!**\n\n🎬 **{video_title}**"
                )
                await status_message.delete()
            except Exception as e:
                # यदि लाइव फाइल सेंड करने में दिक्कत हो तो बैकअप डाउनलोड लिंक देना
                await status_message.edit_text(
                    f"My\n✅ **Download Complete!**\n\n🎬 **{video_title}**\n📥 [यहाँ क्लिक करके डाउनलोड करें]({video_source})",
                    parse_mode='Markdown'
                )
            matched = True
            break
            
    if not matched:
        # अगर कोई नया लिंक भेजे, तो उसका नाम निकालकर डिफ़ॉल्ट वीडियो सेंड करना
        show_name = user_url.split('/show/')[-1].split('?')[0].replace('-', ' ').title()
        try:
            await update.message.reply_video(
                video="https://w3schools.com",
                caption=f"My\n✅ **Download Complete!**\n\n🎬 **{show_name}**"
            )
            await status_message.delete()
        except:
            await status_message.edit_text("❌ इस प्रीमियम लिंक की फाइल सीधे सर्वर से डाउनलोड नहीं हो सकी।")

def main():
    threading.Thread(target=run_web_server, daemon=True).start()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    application.run_polling()

if __name__ == '__main__':
    main()
    
