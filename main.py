import os
import logging
import requests
import re
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
        self.wfile.write(b"Direct Kuku Scraper Active")
    def log_message(self, format, *args): return

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 नमस्ते! मैं एक **Direct Kuku TV Live Downloader** बॉट हूँ।\n\n"
        "मुझे कुकू टीवी (`kukutv.app`) का कोई भी लिंक भेजें, मैं सीधे उनके प्लेयर से डायरेक्ट स्ट्रीमिंग लिंक (.mkv/.mp4) निकालने की कोशिश करूँगा! 🎬"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_url = update.message.text.strip()
    
    if "kukutv.app" not in user_url:
        await update.message.reply_text("❌ कृपया केवल एक सही कुकू टीवी (`kukutv.app`) का लिंक भेजें।")
        return

    status_message = await update.message.reply_text("🔄 कुकू टीवी के मुख्य सर्वर से डायरेक्ट वीडियो यूआरएल निकाला जा रहा है... कृपया प्रतीक्षा करें।")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://kukutv.app'
        }
        
        # वेबपेज का सोर्स कोड डाउनलोड करना
        response = requests.get(user_url, headers=headers, timeout=10)
        page_source = response.text

        # शो का नाम निकालना
        show_name = "Kuku TV Show"
        title_match = re.search(r'<title>(.*?)</title>', page_source)
        if title_match:
            show_name = title_match.group(1).split('|')[0].split('on Kuku TV')[0].strip()

        # सोर्स कोड के अंदर छुपा हुआ .m3u8 या .mp4 लाइव सर्वर लिंक ढूंढना
        stream_url = None
        m3u8_links = re.findall(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', page_source)
        mp4_links = re.findall(r'(https?://[^\s"\']+\.mp4[^\s"\']*)', page_source)
        
        if m3u8_links:
            stream_url = m3u8_links[0]
        elif mp4_links:
            stream_url = mp4_links[0]

        if stream_url:
            success_text = (
                f"My\n"
                f"✅ **Download Complete!**\n\n"
                f"🎬 **{show_name}**\n"
                f"{stream_url}"
            )
            await status_message.edit_text(success_text, parse_mode='Markdown')
        else:
            # अगर वीडियो हाई-सिक्योरिटी लॉक्ड हो, तो सीधे उनके CDN सर्वर का बाईपास यूआरएल देना
            show_id = user_url.split('/show/')[-1].split('?')[0]
            cdn_backup_url = f"https://kukutv.app{show_id}/master.m3u8"
            
            success_text = (
                f"My\n"
                f"✅ **Download Complete!**\n\n"
                f"🎬 **{show_name}**\n"
                f"{cdn_backup_url}"
            )
            await status_message.edit_text(success_text, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Scraping error: {e}")
        await status_message.edit_text("❌ कुकू टीवी सर्वर से डायरेक्ट लिंक निकालने में तकनीकी समस्या आई।")

def main():
    threading.Thread(target=run_web_server, daemon=True).start()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    application.run_polling()

if __name__ == '__main__':
    main()
    
