import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- सेटिंग्स ---
BOT_TOKEN = "8306462663:AAE_p6_Al0yfvi-Ha_A34nD3Dx2_3Ndtrgc"
ADMIN_ID = 123456789  # ⚠️ यहाँ अपनी असली Telegram User ID डालें (ताकि सिर्फ आप अप्रूव कर सकें)

# 🔒 स्वीकृत यूजर्स की लिस्ट (शुरुआत में आप खुद एडमिन के रूप में इसमें शामिल हैं)
APPROVED_USERS = {ADMIN_ID}

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

# 1. /start कमांड फंक्शन
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    user = update.effective_user
    
    # ❌ अगर यूजर अप्रूव्ड नहीं है
    if user.id not in APPROVED_USERS:
        # यूजर को यह मैसेज दिखेगा (जैसा आपने माँगा था)
        await update.message.reply_text(
            f"👋 Hi {user.first_name}! You need admin approval.\n"
            f"Your Telegram ID: `{user.id}`"
        )
        
        # 🕵️‍♂️ एडमिन (आपको) अलर्ट मैसेज जाएगा कि इस यूजर को अप्रूव करना है
        admin_alert = (
            f"👤 **New Approval Request!**\n\n"
            f"📛 Name: {user.full_name}\n"
            f"🆔 ID: `{user.id}`\n"
            f"🔗 Username: @{user.username if user.username else 'None'}\n\n"
            f"इस यूजर को अप्रूव करने के लिए यह कमांड कॉपी करके भेजें:\n"
            f"`/approve {user.id}`"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_alert, parse_mode='Markdown')
        except Exception as e:
            logging.error(f"Failed to send alert to admin: {e}")
        return

    # ✅ अगर यूजर पहले से अप्रूव्ड है, तो उसे सीधा स्वागत संदेश दिखेगा
    await update.message.reply_text( 
        "👋 नमस्ते! **Vikash Raj Bot** में आपका स्वागत है। 🤖 मैं आपका Kuku TV Direct Downloader बॉट हूँ।\n\n" 
        "मुझे कुकू टीवी का लिंक भेजें, मैं आपको तुरंत डायरेक्ट डाउनलोड लिंक दूंगा! 🎬"
    )

# 2. एडमिन के लिए /approve कमांड (सिर्फ आप किसी को अप्रूव कर सकते हैं)
async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    # सुरक्षा जांच: क्या कमांड भेजने वाला असली एडमिन है?
    if user.id != ADMIN_ID:
        return
        
    if not context.args:
        await update.message.reply_text("❌ कृपया यूजर की ID भी साथ में लिखें। उदाहरण: `/approve 1106698349`", parse_mode='Markdown')
        return
        
    try:
        target_id = int(context.args[0])
        APPROVED_USERS.add(target_id)  # यूजर आईडी को लिस्ट में जोड़ें
        
        await update.message.reply_text(f"✅ User ID `{target_id}` को सफलतापूर्वक अप्रूव कर दिया गया है!", parse_mode='Markdown')
        
        # यूजर को सूचित करें कि उसका बॉट चालू हो गया है
        try:
            await context.bot.send_message(
                chat_id=target_id, 
                text="🎉 **बधाई हो!** एडमिन (**Vikash Raj**) ने आपका अनुरोध स्वीकार कर लिया है।\n\n"
                     "अब आप बॉट का इस्तेमाल कर सकते हैं! दोबारा चालू करने के लिए /start दबाएं।",
                parse_mode='Markdown'
            )
        except Exception as e:
            logging.error(f"Could not notify user {target_id}: {e}")
            
    except ValueError:
        await update.message.reply_text("❌ कृपया एक सही संख्यात्मक (Numeric) ID दर्ज करें।")

# 3. लिंक हैंडलर फंक्शन (यहाँ भी सुरक्षा लगी है)
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    user = update.effective_user
    
    # बिना अप्रूवल के लिंक काम नहीं करेगा
    if user.id not in APPROVED_USERS:
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
            extracted_name = user_url.split('/show/')[-1].split('?').replace('-', ' ').title() 
        except: 
            extracted_name = "Kuku TV Microdrama" 
        await status_message.edit_text( 
            f"❌ **{extracted_name}** की फाइल अभी डेटाबेस में उपलब्ध नहीं है।\n" 
            "कृपया एडमिन द्वारा सेट किया गया सही लिंक भेजें।" 
        )

def main(): 
    threading.Thread(target=run_web_server, daemon=True).start() 
    application = Application.builder().token(BOT_TOKEN).build() 
    
    # कमांड्स को जोड़ना
    application.add_handler(CommandHandler("start", start)) 
    application.add_handler(CommandHandler("approve", approve_user)) # नई अप्रूव कमांड
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)) 
    
    application.run_polling()

if __name__ == '__main__': 
    main()
    
