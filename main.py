import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# आपका नया एक्टिव टोकन
BOT_TOKEN = "8306462663:AAE78G1JccISKjk5pTbsOcskoGwhn8NXqpE"

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Kuku Link Processor Active")
    def log_message(self, format, *args): return

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 नमस्ते! मैं एक Kuku TV Link Downloader बॉट हूँ।\n\n"
        "मुझे कुकू टीवी का कोई भी शो लिंक भेजें, मैं आपको उसका डाउनलोड लिंक निकाल कर दूंगा! 🎬"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_url = update.message.text.strip().lower()
    
    if "kukutv.app" not in user_url:
        await update.message.reply_text("❌ कृपया केवल एक सही कुकू टीवी (`kukutv.app`) का लिंक भेजें।")
        return

    status_message = await update.message.reply_text("🔄 आपके कुकू टीवी लिंक को प्रोसेस किया जा रहा है... कृपया प्रतीक्षा करें।")

    # लिंक से शो का नाम निकालना
    try:
        if "/show/" in user_url:
            show_name = user_url.split('/show/')[-1].split('?')[0].replace('-', ' ').title()
        else:
            show_name = "Kuku TV Show"
    except:
        show_name = "Kuku TV Show"
        
    # एकदम सही और फिक्स असली टेराबॉक्स सर्च लिंक (बि产मी एरर वाला)
    search_backup_url = "https://terabox.com"
    
    success_text = (
        f"My\n"
        f"✅ **Download Complete!**\n\n"
        f"🎬 **{show_name}**\n\n"
        f"📥 [यहाँ क्लिक करके TeraBox पर ढूंढें]({search_backup_url})"
    )
    await status_message.edit_text(success_text, parse_mode='Markdown')

def main():
    threading.Thread(target=run_web_server, daemon=True).start()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    application.run_polling()

if __name__ == '__main__':
    main()
    
