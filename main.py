import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ⚠️ आपका नया टोकन यहाँ जोड़ दिया गया है
BOT_TOKEN = "8306462663:AAE78G1JccISKjk5pTbsOcskoGwhn8NXqpE"

# 🎬 डेटाबेस: यहाँ कुकू टीवी लिंक्स और उनके सामने टेराबॉक्स/जीड्राइव लिंक्स सेट हैं
DATABASE = {
    "https://kukutv.app": {
        "title": "The Key Lord | Thriller Series",
        "download_url": "https://terabox.com" # यहाँ बाद में अपना असली फाइल लिंक बदल सकते हैं
    },
    "https://kukutv.app": {
        "title": "The Gangster King | Action Series",
        "download_url": "https://terabox.com"
    }
}

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is active")
    def log_message(self, format, *args): return

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 नमस्ते! मैं आपका नया Kuku TV Auto-Downloader बॉट हूँ।\n\n"
        "मुझे कुकू टीवी का लिंक भेजें, मैं आपको तुरंत डाउनलोड फाइल दे दूंगा! 🎬"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_link = update.message.text.strip()
    status_message = await update.message.reply_text("🔄 आपके लिंक से video खोजी जा रही है... कृपया प्रतीक्षा करें।")

    matched = False
    for db_link, video_info in DATABASE.items():
        if db_link in user_link or user_link in db_link or "the-key-lord" in user_link.lower():
            video_title = video_info["title"]
            video_url = video_info["download_url"]
            success_text = (
                f"My\n"
                f"✅ **Download Complete!**\n\n"
                f"🎬 **{video_title}**\n"
                f"{video_url}"
            )
            await status_message.edit_text(success_text, parse_mode='Markdown')
            matched = True
            break
            
    if not matched:
        await status_message.edit_text(
            "❌ इस लिंक की फाइल अभी डेटाबेस में उपलब्ध नहीं है।\n"
            "कृपया एडमिन द्वारा सेट किया गया सही लिंक भेजें।"
        )

def main():
    threading.Thread(target=run_web_server, daemon=True).start()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    application.run_polling()

if __name__ == '__main__':
    main()
