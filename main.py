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
    # 🌟 आपका नया हिंदी स्वागत संदेश यहाँ सेट कर दिया गया है
    await update.message.reply_text( 
        "👋 नमस्ते! Vikash Raj Bot में आपका स्वागत है। 🤖 मैं आपका Kuku TV Direct Downloader बॉट हूँ।\n\n" 
        "मुझे कुकू टीवी का लिंक भेजें, मैं आपको तुरंत डायरेक्ट डाउनलोड लिंक दूंगा! 🎬"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    user_url = update.message.text.strip().lower() 
    if "kukutv.app" not in user_url and "kuku.com" not in user_url: 
        await update.message.reply_text("❌ कृपया केवल एक सही कुकू टीवी का लिंक भेजें।") 
        return 
        
    status_message = await update.message.reply_text("🔄 आपके लिंक से वीडियो फाइल खोजी जा रही है... कृपया प्रतीक्षा करें।") 
    matched = False 
    
    for show_key, info in SHOWS_DATABASE.items(): 
        if show_key in user_url: 
            show_title = info["title"] 
            download_link = info["download_url"] 
            
            # सक्सेस मैसेज (इसमें भी आपका नाम सेट है)
            success_text = ( 
                f"🤖 bot: Vikash Raj \n\n" 
                f"✅  Download Complete! \n\n" 
                f"🎬  {show_title}\n\n" 
                f"📥 [यहाँ क्लिक करके सीधे .mkv फाइल डाउनलोड करें]({download_link})" 
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
            f"❌ **{extracted_name}** की फाइल अभी डेटाबेस में उपलब्ध नहीं है।\n" 
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
    
