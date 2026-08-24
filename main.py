import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# आपका टोकन
BOT_TOKEN = "8306462663:AAE_p6_Al0yfvi-Ha_A34nD3Dx2_3Ndtrgc"

# 🎬 गूगल ड्राइव डेटाबेस
SHOWS_DATABASE = { 
    "mera-inteqaam-dekhegi": { 
        "title": "Mera Inteqaam Dekhegi | Full Episode", 
        "download_url": "https://google.com" 
    }, 
    "legacy-of-betrayal": { 
        "title": "Legacy of Betrayal | Full Show", 
        "download_url": "https://google.com" 
    }
}

class HealthCheckHandler(BaseHTTPRequestHandler): 
    def do_GET(self): 
        self.send_response(200) 
        self.send_header("Content-type", "text/plain") 
        self.end_headers() 
        self.wfile.write(b"Google Drive Engine Active") 
    def log_message(self, format, *args): 
        return

def run_web_server(): 
    port = int(os.environ.get("PORT", 8080)) 
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler) 
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    # यहाँ इंग्लिश में आपका नाम सेट कर दिया गया है
    await update.message.reply_text( 
        "👋 Hello! I am **Vikash Raj**, your Kuku TV Direct Downloader Bot.\n\n" 
        "Send me any Kuku TV link, and I will instantly provide you the direct download link! 🎬" 
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    user_url = update.message.text.strip().lower() 
    if "kukutv.app" not in user_url and "kuku.com" not in user_url: 
        await update.message.reply_text("❌ Please send a valid Kuku TV link.") 
        return 
        
    status_message = await update.message.reply_text("🔄 Checking your link, please wait...") 
    matched = False 
    
    for show_key, info in SHOWS_DATABASE.items(): 
        if show_key in user_url: 
            show_title = info["title"] 
            download_link = info["download_url"] 
            
            # सक्सेस मैसेज में भी क्रेडिट चेंज कर दिया गया है
            success_text = ( 
                f"🤖 **Bot By: Vikash Raj**\n\n" 
                f"✅ **Download Complete!**\n\n" 
                f"🎬 **{show_title}**\n\n" 
                f"📥 [Click here to download .mkv file directly]({download_link})" 
            ) 
            await status_message.edit_text(success_text, parse_mode='Markdown', disable_web_page_preview=True) 
            matched = True 
            break 
            
    if not matched: 
        try: 
            extracted_name = user_url.split('/show/')[-1].split('?')[0].replace('-', ' ').title() 
        except: 
            extracted_name = "Kuku TV Microdrama" 
        await status_message.edit_text( 
            f"❌ **{extracted_name}** is not available in our database yet.\n" 
            "Please try again later or contact the admin." 
        )

def main(): 
    threading.Thread(target=run_web_server, daemon=True).start() 
    application = Application.builder().token(BOT_TOKEN).build() 
    application.add_handler(CommandHandler("start", start)) 
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)) 
    application.run_polling()

if __name__ == '__main__': 
    main()
    
