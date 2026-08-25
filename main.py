import os
import boto3
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Render के Environment Variables से क्रेडेंशियल्स लेना
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
R2_ENDPOINT = os.getenv("R2_ENDPOINT_URL")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
PUBLIC_R2_URL = os.getenv("R2_PUBLIC_URL")

# Cloudflare R2 क्लाइंट सेटअप
r2_client = boto3.client(
    service_name='s3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name='auto'
)

def get_kuku_media(user_url):
    """
    पब्लिक बाईपास API का उपयोग करके Kuku लिंक से डायरेक्ट ऑडियो निकालना।
    """
    try:
        api_url = f"https://bhadoo.cc{user_url}"
        response = requests.get(api_url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            download_url = data.get("file") or data.get("direct_link")
            title = data.get("title") or "kuku_audio"
            clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).rstrip()
            return download_url, clean_title
    except Exception as e:
        print(f"API Error: {e}")
    return None, None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 नमस्ते! मैं KukuTV/FM Downloader बोट हूँ।\n\n"
        "मुझे कोई भी Kuku लिंक भेजें, मैं उसे डाउनलोड करके आपके Cloudflare R2 पर अपलोड कर दूँगा।"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_url = update.message.text
    
    if "kuku" not in user_url.lower():
        await update.message.reply_text("❌ कृपया केवल वैध KukuTV या KukuFM का लिंक ही भेजें।")
        return

    status = await update.message.reply_text("🔍 लिंक को बाईपास किया जा रहा है... कृपया प्रतीक्षा करें।")
    
    # 1. API से डायरेक्ट लिंक निकालें
    media_url, title = get_kuku_media(user_url)
    
    if not media_url:
        await status.edit_text("❌ मीडिया लिंक निकालने में विफल। लिंक गलत है या API अभी व्यस्त है।")
        return

    await status.edit_text(f"📥 डाउनलोडिंग शुरू: {title}...")
    local_file = f"{title}.mp3"
    
    # 2. फाइल को सर्वर पर टेम्पररी डाउनलोड करना
    try:
        with requests.get(media_url, stream=True) as r:
            r.raise_for_status()
            with open(local_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except Exception as e:
        await status.edit_text(f"❌ फाइल डाउनलोड करने में त्रुटि: {str(e)}")
        return

    await status.edit_text("☁️ Cloudflare R2 क्लाउड पर अपलोड किया जा रहा है...")
    
    # 3. Cloudflare R2 पर अपलोड करना
    r2_key = f"kukushare/{local_file}"
    try:
        r2_client.upload_file(
            local_file, 
            BUCKET_NAME, 
            r2_key, 
            ExtraArgs={'ContentType': 'audio/mpeg'}
        )
        
        final_url = f"{PUBLIC_R2_URL}/{r2_key}"
        
        await status.edit_text(
            f"✅ **सफलतापूर्वक अपलोड हो गया!**\n\n"
            f"🎵 **नाम:** {title}\n"
            f"🔗 [यहाँ क्लिक करके डाउनलोड करें]({final_url})",
            parse_mode="Markdown"
        )
    except Exception as e:
        await status.edit_text(f"❌ R2 अपलोड फेल हुआ: {str(e)}")
    finally:
        if os.path.exists(local_file):
            os.remove(local_file)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
    
