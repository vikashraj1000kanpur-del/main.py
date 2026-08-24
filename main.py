import os
import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- सेटिंग्स ---
BOT_TOKEN = "8306462663:AAE_p6_Al0yfvi-Ha_A34nD3Dx2_3Ndtrgc"
ADMIN_ID = 8529632128  # ✅ विकास राज, आपकी असली Telegram ID यहाँ सेट कर दी गई है

DB_FILE = "approved_users.json"

# --- डेटाबेस फंक्शन्स (यूजर्स को हमेशा के लिए सुरक्षित रखने के लिए) ---
def load_approved_users():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                return set(data)
        except Exception as e:
            logging.error(f"Error loading DB: {e}")
            return {ADMIN_ID}
    return {ADMIN_ID}

def save_approved_user(user_id):
    approved_users = load_approved_users()
    approved_users.add(user_id)
    try:
        with open(DB_FILE, "w") as f:
            json.dump(list(approved_users), f)
    except Exception as e:
        logging.error(f"Error saving to DB: {e}")

# 🎬 कुकू टीवी शोज़ का डेटाबेस
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

# --- वेब सर्वर (Render/Koyeb के लिए) ---
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

# --- बॉट कमांड्स ---

# 1. /start कमांड
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    user = update.effective_user
    current_approved = load_approved_users()
    
    # ❌ अगर यूजर अप्रूव्ड नहीं है, तो बॉट उसकी ID जनरेट करके दिखाएगा
    if user.id not in current_approved:
        await update.message.reply_text(
            f"👋 Hi {user.first_name}! You need admin approval.\n"
            f"Your Telegram ID: `{user.id}`",
            parse_mode='Markdown'
        )
        
        # 🕵️‍♂️ यह अलर्ट सीधे आपके (विकास राज) पास आएगा
        admin_alert = (
            f"👤 **New Approval Request!**\n\n"
            f"📛 Name: {user.full_name}\n"
            f"🆔 ID: `{user.id}`\n"
            f"🔗 Username: @{user.username if user.username else 'None'}\n\n"
            f"इस यूजर को अप्रूव करने के लिए नीचे दी गई कमांड पर क्लिक करके भेजें:\n"
            f"`/approve {user.id}`"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_alert, parse_mode='Markdown')
        except Exception as e:
            logging.error(f"Failed to send alert to admin: {e}")
        return

    # ✅ अगर यूजर अप्रूव्ड है (या आप खुद हैं)
    await update.message.reply_text( 
        "👋 नमस्ते! **Vikash Raj Bot** में आपका स्वागत है। 🤖 मैं आपका Kuku TV Direct Downloader बॉट हूँ।\n\n" 
        "मुझे कुकू टीवी का लिंक भेजें, मैं आपको तुरंत डायरेक्ट डाउनलोड लिंक दूंगा! 🎬"
    )

# 2. /approve कमांड (सिर्फ विकास राज के लिए काम करेगी)
async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        return
        
    if not context.args:
        await update.message.reply_text("❌ कृपया आईडी साथ में लिखें। उदाहरण: `/approve 1106698349`", parse_mode='Markdown')
        return
        
    try:
        target_id = int(context.args[0])
        save_approved_user(target_id)
        
        await update.message.reply_text(f"✅ User ID `{target_id}` को सफलतापूर्वक अप्रूव कर दिया गया है!", parse_mode='Markdown')
        
        # यूजर को ऑटो-मैसेज जाएगा कि वह अब बॉट इस्तेमाल कर सकता है
        try:
            await context.bot.send_message(
                chat_id=target_id, 
                text="🎉 **बधाई हो!** एडमिन (**Vikash Raj**) ने आपका अनुरोध स्वीकार कर लिया है।\n\n"
                     "अब आप बॉट का इस्तेमाल कर सकते हैं! दोबारा चालू करने के लिए /start दबाएं।",
                parse_mode='Markdown'
            )
        except Exception as e:
            logging.error(f"Could not notify user {target_id}: {e}")
            
    except (ValueError, IndexError):
        await update.message.reply_text("❌ कृपया एक सही Telegram ID दर्ज करें।")

# 3. लिंक हैंडलर फंक्शन
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    user = update.effective_user
    current_approved = load_approved_users()
    
    if user.id not in current_approved:
        await update.message.reply_text("❌ आपको इस बॉट को इस्तेमाल करने की अनुमति नहीं है। कृपया पहले एडमिन से अप्रूवल लें।")
        return

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
            
            success_text = ( 
                f"🤖 **बॉट बाय: Vikash Raj**\n\n" 
                f"✅ **Download Complete!**\n\n" 
                f"🎬 **{show_title}**\n\n" 
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
    application.add_handler(CommandHandler("approve", approve_user))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)) 
    
    application.run_polling()

if __name__ == '__main__': 
    main()
    
