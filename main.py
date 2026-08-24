import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ContextTypes

# --- SHOWS DATABASE (Add your shows and download links here) ---
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

# --- HEALTH CHECK SERVER (To keep the bot alive on Render/Koyeb) ---
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

# --- TELEGRAM BOT COMMANDS ---

# 1. /start Command (English Text with your name)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I am **Vikash Raj**, your Kuku TV Direct Downloader Bot.\n\n"
        "Send me any Kuku TV link, and I will instantly provide you the direct download link! 🎬"
    )

# 2. Link Handler Function
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_url = update.message.text.strip().lower()
    
    # URL Validation
    if "kukutv.app" not in user_url and "kuku.com" not in user_url:
        await update.message.reply_text("❌ Please send a valid Kuku TV link.")
        return
        
    status_message = await update.message.reply_text("🔄 Checking your link, please wait...")
    
    matched = False
    for show_key, info in SHOWS_DATABASE.items():
        if show_key in user_url:
            show_title = info["title"]
            download_link = info["download_url"]
            
            # Success Message (With your credits in English)
            success_text = (
                f"🤖 **Bot By: Vikash Raj**\n\n"
                f"✅ **Download Complete!**\n\n"
                f"🎬 **{show_title}**\n\n"
                f"📥 [Click here to download .mkv file directly]({download_link})"
            )
            
            await status_message.edit_text(success_text, parse_mode="Markdown", disable_web_page_preview=True)
            matched = True
            break
            
    if not matched:
        await status_message.edit_text("❌ Sorry! This show is not available in our database yet.")
        
