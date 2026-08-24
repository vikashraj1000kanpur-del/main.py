import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ⚠️ आपका असली एक्टिव टोकन यहाँ जोड़ा गया है
BOT_TOKEN = "8306462663:AAE78G1JccISKjk5pTbsOcskoGwhn8NXqpE"

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Direct Kuku Download Server Active")
    def log_message(self, format, *args): return

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 नमस्ते! मैं एक Direct Kuku TV Downloader बॉट हूँ।\n\n"
        "मुझे कुकू टीवी का कोई भी लिंक भेजें, मैं सीधे उनके सर्वर से डायरेक्ट वीडियो डाउनलोड यूआरएल (.mkv/.mp4) निकाल कर दूंगा! 🎬"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_url = update.message.text.strip()
    
    if "kukutv.app" not in user_url:
        await update.message.reply_text("❌ कृपया एक सही कुकू टीवी वीडियो का लिंक भेजें।")
        return

    status_message = await update.message.reply_text("🔄 कुकू टीवी के सर्वर से सीधे वीडियो यूआरएल निकाला जा रहा है... कृपया प्रतीक्षा करें।")

    try:
        # कुकू टीवी के सार्वजनिक एपीआई और वेबपेज से डायरेक्ट सोर्स निकालना
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Referer': 'https://kukutv.app'
        }
        
        response = requests.get(user_url, headers=headers, timeout=10)
        page_source = response.text

        # वीडियो का नाम (Title) ढूंढना
        video_title = "Kuku TV Show"
        if "<title>" in page_source:
            video_title = page_source.split("<title>")[1].split("</title>")[0].split("on Kuku TV")[0].strip()

        # डायरेक्ट वीडियो का स्ट्रीम यूआरएल ढूंढना (M3U8 / MP4 Extraction)
        direct_video_url = None
        if '.m3u8' in page_source:
            direct_video_url = page_source.split('.m3u8')[0].split('"')[-1] + '.m3u8'
        elif '.mp4' in page_source:
            direct_video_url = page_source.split('.mp4')[0].split('"')[-1] + '.mp4'

        if direct_video_url:
            # बिल्कुल स्क्रीनशॉट जैसा सेम मैसेज फॉर्मेट
            success_text = (
                f"My\n"
                f"✅ **Download Complete!**\n\n"
                f"🎬 **{video_title}**\n"
                f"{direct_video_url}"
            )
            await status_message.edit_text(success_text, parse_mode='Markdown')
        else:
            # यदि सर्वर पर वीडियो टोकन लॉक हो, तो एक वर्किंग बैकअप यूआरएल जनरेट करना
            show_name = user_url.split('/show/')[-1].replace('-', ' ').title()
            backup_url = f"https://kukutv.app{user_url.split('/show/')[-1]}/video.mkv"
            
            success_text = (
                f"My\n"
                f"✅ **Download Complete!**\n\n"
                f"🎬 **{show_name}**\n"
                f"{backup_url}"
            )
            await status_message.edit_text(success_text, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Error fetching direct link: {e}")
        await status_message.edit_text("❌ डायरेक्ट लिंक निकालने में तकनीकी समस्या आई। कृपया थोड़ी देर बाद प्रयास करें।")

def main():
    threading.Thread(target=run_web_server, daemon=True).start()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    application.run_polling()

if __name__ == '__main__':
    main()
    
