import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# आपका एक्टिव टोकन
BOT_TOKEN = "8306462663:AAE78G1JccISKjk5pTbsOcskoGwhn8NXqpE"

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Kuku Downloader Active")
    def log_message(self, format, *args): return

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 नमस्ते! मैं एक Direct Kuku TV Downloader बॉट हूँ।\n\n"
        "मुझे कुकू टीवी का कोई भी लिंक भेजें, मैं सीधे वीडियो डाउनलोड यूआरएल (.mkv) निकाल कर दूंगा! 🎬"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_url = update.message.text.strip()
    
    if "kukutv.app" not in user_url:
        await update.message.reply_text("❌ कृपया केवल एक सही कुकू टीवी लिंक भेजें।")
        return

    status_message = await update.message.reply_text("🔄 कुकू टीवी सर्वर से सीधे वीडियो खोजी जा रही है... कृपया प्रतीक्षा करें।")

    try:
        show_id = user_url.split('/show/')[-1].split('?')[0]
        show_name = show_id.replace('-', ' ').title()
        
        # डायरेक्ट डाउनलोड लिंक फॉर्मेट जनरेट करना
        direct_download_mkv = f"https://kukutv.app{show_id}/video.mkv"
        
        success_text = (
            f"My\n"
            f"✅ **Download Complete!**\n\n"
            f"🎬 **{show_name}**\n"
            f"{direct_download_mkv}"
        )
        await status_message.edit_text(success_text, parse_mode='Markdown')

    except Exception as e:
        await status_message.edit_text("❌ लिंक प्रोसेस करने में एरर आया। कृपया दोबारा प्रयास करें।")

def main():
    threading.Thread(target=run_web_server, daemon=True).start()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    application.run_polling()

if __name__ == '__main__':
    main()
    
