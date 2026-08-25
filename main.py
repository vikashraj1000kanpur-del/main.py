import os
import requests
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- आपके बिल्कुल सही क्रेडेंशियल्स सीधे कोड में यहाँ सेट हैं ---
BOT_TOKEN = "8306462663:AAEzmQ8ayW2LwiFbxyZEHzCIXoZ-gGgx5jI"
SUPABASE_URL = "https://anxaejixflcatlvdpovy.supabase.co"
SUPABASE_KEY = "sb_publishable_HgSurnD3QUqmto0VQvtuzA_ih3a4IqF"
BUCKET_NAME = "kukushare"  # आपके Supabase बकेट का नाम

def get_kuku_all_episodes(user_url):
    try:
        api_url = f"https://bhadoo.cc{user_url}"
        response = requests.get(api_url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            episodes = data.get("episodes") or data.get("playlist")
            title = data.get("title") or "kuku_full_show"
            clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).rstrip()
            
            if not episodes and (data.get("file") or data.get("direct_link")):
                episodes = [data.get("file") or data.get("direct_link")]
                
            return episodes, clean_title
    except Exception as e:
        print(f"API Error: {e}")
    return None, None

def merge_videos(video_files, output_filename):
    list_file = "file_list.txt"
    with open(list_file, "w") as f:
        for video in video_files:
            f.write(f"file '{video}'\n")
            
    command = f"ffmpeg -f concat -safe 0 -i {list_file} -c copy {output_filename} -y"
    process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if os.path.exists(list_file):
        os.remove(list_file)
        
    return process.returncode == 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 नमस्ते! मैं KukuTV/FM Full Length Downloader बोट हूँ।\n\n"
        "मुझे कोई भी Kuku लिंक भेजें। मैं उसके सभी पार्ट्स को जोड़कर (Merge) एक "
        "फुल-लेंथ वीडियो सीधे आपके Supabase क्लाउड पर अपलोड कर दूँगा।"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_url = update.message.text
    if "kuku" not in user_url.lower():
        await update.message.reply_text("❌ कृपया केवल वैध KukuTV या KukuFM का लिंक ही भेजें।")
        return

    status = await update.message.reply_text("🔍 लिंक को प्रोसेस किया जा रहा है... कृपया प्रतीक्षा करें।")
    episodes_list, title = get_kuku_all_episodes(user_url)
    
    if not episodes_list:
        await status.edit_text("❌ वीडियो पार्ट्स निकालने में विफल। लिंक पुराना है या सुरक्षित है।")
        return

    total_parts = len(episodes_list)
    await status.edit_text(f"📥 कुल {total_parts} पार्ट्स मिले। डाउनलोडिंग शुरू की जा रही है...")
    
    downloaded_files = []
    
    for index, media_url in enumerate(episodes_list):
        await status.edit_text(f"📥 डाउनलोड हो रहा है... पार्ट: {index + 1}/{total_parts}")
        part_filename = f"part_{index}.mp4"
        
        try:
            with requests.get(media_url, stream=True) as r:
                r.raise_for_status()
                with open(part_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            downloaded_files.append(part_filename)
        except Exception as e:
            await status.edit_text(f"❌ पार्ट {index + 1} डाउनलोड करने में एरर आया: {str(e)}")
            for f in downloaded_files: 
                if os.path.exists(f): os.remove(f)
            return

    await status.edit_text("🎬 सभी पार्ट्स को जोड़कर एक full video बनाया जा रहा है (Merging)...")
    final_output = f"{title}_Full.mp4"
    
    merge_success = merge_videos(downloaded_files, final_output)
    
    for f in downloaded_files:
        if os.path.exists(f): os.remove(f)
        
    if not merge_success or not os.path.exists(final_output):
        await status.edit_text("❌ वीडियो मर्ज करने में तकनीकी खराबी आई।")
        return

    await status.edit_text("☁️ फुल वीडियो को आपके Supabase क्लाउड पर अपलोड किया जा रहा है...")
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{final_output}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY
    }
    
    try:
        with open(final_output, 'rb') as f:
            res = requests.post(upload_url, headers=headers, files={'file': f})
            
        if res.status_code == 200:
            final_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{final_output}"
            await status.edit_text(
                f"✅ **फुल वीडियो सफलतापूर्वक तैयार है!**\n\n"
                f"🎬 **शो का नाम:** {title}\n"
                f"📦 **कुल जोड़े गए पार्ट्स:** {total_parts}\n\n"
                f"🔗 [यहाँ क्लिक करके फुल वीडियो डाउनलोड करें]({final_url})", 
                parse_mode="Markdown"
            )
        else:
            await status.edit_text(f"❌ क्लाउड अपलोड फेल हुआ: {res.text}")
    except Exception as e:
        await status.edit_text(f"❌ अपलोड एरर: {str(e)}")
    finally:
        if os.path.exists(final_output):
            os.remove(final_output)

if __name__ == "__main__":
    # अब यह स्टेबल Python 3.11 पर बिना किसी एरर के दौड़ेगा
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("बोट सफलतापूर्वक चालू हो गया है...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
            
