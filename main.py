import os
import requests
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Render के Environment Variables से क्रेडेंशियल्स लेना (इन्हें कोड में डायरेक्ट मत लिखना)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = "kukushare"  # आपके Supabase बकेट का नाम

def get_kuku_all_episodes(user_url):
    """
    KukuTV/FM लिंक से सभी छोटे वीडियो पार्ट्स (Episodes) के लिंक्स और टाइटल निकालना।
    """
    try:
        # पब्लिक बाईपास API एंडपॉइंट
        api_url = f"https://bhadoo.cc{user_url}"
        response = requests.get(api_url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # अगर API सभी एपिसोड्स की लिस्ट (Array) देता है
            episodes = data.get("episodes") or data.get("playlist")
            title = data.get("title") or "kuku_full_show"
            
            # टाइटल से स्पेशल कैरेक्टर हटाना ताकि फाइल नाम में एरर न आए
            clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).rstrip()
            
            # अगर डायरेक्ट लिस्ट नहीं है और सिर्फ सिंगल लिंक आ रहा है, तो उसे लिस्ट में बदल लें
            if not episodes and (data.get("file") or data.get("direct_link")):
                episodes = [data.get("file") or data.get("direct_link")]
                
            return episodes, clean_title
    except Exception as e:
        print(f"API Error: {e}")
    return None, None

def merge_videos(video_files, output_filename):
    """
    FFmpeg का उपयोग करके सभी डाउनलोड किए गए छोटे वीडियो पार्ट्स को एक सिंगल फाइल में मर्ज करना।
    """
    list_file = "file_list.txt"
    # एक टेक्स्ट फाइल बनाना जिसमें सभी वीडियो फाइल्स की लिस्ट होगी
    with open(list_file, "w") as f:
        for video in video_files:
            f.write(f"file '{video}'\n")
            
    # FFmpeg concat कमांड चलाकर बिना क्वालिटी खोए वीडियो को आपस में जोड़ना
    command = f"ffmpeg -f concat -safe 0 -i {list_file} -c copy {output_filename} -y"
    
    # कमांड को बैकएंड सर्वर पर रन करना
    process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # काम पूरा होने के बाद लिस्ट फाइल को डिलीट करना
    if os.path.exists(list_file):
        os.remove(list_file)
        
    return process.returncode == 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 नमस्ते! मैं KukuTV/FM Full Length Downloader बोट हूँ।\n\n"
        "मुझे कोई भी Kuku लिंक भेजें। मैं उसके सभी छोटे वीडियो पार्ट्स को आपस में जोड़कर (Merge) एक "
        "फुल-लेंथ सिंगल वीडियो सीधे आपके Supabase क्लाउड पर अपलोड कर दूँगा और आपको डाउनलोड लिंक दूंगा।"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_url = update.message.text
    if "kuku" not in user_url.lower():
        await update.message.reply_text("❌ कृपया केवल वैध KukuTV या KukuFM का लिंक ही भेजें।")
        return

    status = await update.message.reply_text("🔍 लिंक को प्रोसेस किया जा रहा है... कृपया प्रतीक्षा करें।")
    
    # 1. API से सभी वीडियो पार्ट्स की लिस्ट और शो का नाम निकालना
    episodes_list, title = get_kuku_all_episodes(user_url)
    
    if not episodes_list:
        await status.edit_text("❌ वीडियो पार्ट्स निकालने में विफल। लिंक पुराना है या सुरक्षित है।")
        return

    total_parts = len(episodes_list)
    await status.edit_text(f"📥 कुल {total_parts} पार्ट्स मिले। डाउनलोडिंग शुरू की जा रही है...")
    
    downloaded_files = []
    
    # 2. सभी वीडियो पार्ट्स को एक-एक करके सर्वर पर डाउनलोड करना
    for index, media_url in enumerate(episodes_list):
        await status.edit_text(f"📥 डाउनलोड हो रहा है पार्ट: {index + 1}/{total_parts}...")
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
            # सर्वर साफ करने के लिए पुराने डाउनलोड पार्ट्स डिलीट करना
            for f in downloaded_files: 
                if os.path.exists(f): os.remove(f)
            return

    # 3. FFmpeg के जरिए वीडियो मर्ज (Merge) करना
    await status.edit_text("🎬 सभी पार्ट्स को जोड़कर एक फुल-लेंथ वीडियो बनाया जा रहा है (Merging)...")
    final_output = f"{title}_Full.mp4"
    
    merge_success = merge_videos(downloaded_files, final_output)
    
    # मर्ज होने के बाद छोटे अस्थायी पार्ट्स को डिलीट करना
    for f in downloaded_files:
        if os.path.exists(f): os.remove(f)
        
    if not merge_success or not os.path.exists(final_output):
        await status.edit_text("❌ वीडियो मर्ज करने में तकनीकी खराबी आई।")
        return

    # 4. फुल वीडियो फाइल को Supabase Storage पर अपलोड करना
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
            # फाइनल डायरेक्ट डाउनलोड लिंक जेनरेट करना
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
        # अंतिम काम पूरा होने के बाद मुख्य फाइल भी सर्वर से डिलीट करना ताकि स्पेस न भरे
        if os.path.exists(final_output):
            os.remove(final_output)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("बोट सफलतापूर्वक चालू हो गया है...")
    app.run_polling()
    
