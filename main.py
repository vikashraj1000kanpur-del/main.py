import os
import time
import requests
import subprocess

# --- आपके बिल्कुल सही क्रेडेंशियल्स बिना किसी बदलाव के यहाँ सेट हैं ---
BOT_TOKEN = "8306462663:AAEzmQ8ayW2LwiFbxyZEHzCIXoZ-gGgx5jI"
SUPABASE_URL = "https://anxaejixflcatlvdpovy.supabase.co"
SUPABASE_KEY = "sb_publishable_HgSurnD3QUqmto0VQvtuzA_ih3a4IqF"
BUCKET_NAME = "kukushare"

BASE_URL = f"https://telegram.org{BOT_TOKEN}"

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

def send_message(chat_id, text, reply_to_message_id=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    res = requests.post(url, json=payload)
    return res.json()

def edit_message(chat_id, message_id, text):
    url = f"{BASE_URL}/editMessageText"
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def handle_bot_logic(msg):
    text = msg.get("text", "")
    chat_id = msg["chat"]["id"]
    msg_id = msg["message_id"]

    if text.startswith("/start"):
        send_message(chat_id, "👋 नमस्ते! मैं KukuTV/FM Full Length Downloader बोट हूँ।\n\nमुझे कोई भी Kuku लिंक भेजें। मैं उसके सभी पार्ट्स को जोड़कर (Merge) एक फुल-लेंथ वीडियो सीधे आपके Supabase क्लाउड पर अपलोड कर दूँगा।")
        return

    if "kuku" not in text.lower():
        send_message(chat_id, "❌ कृपया केवल वैध KukuTV या KukuFM का लिंक ही भेजें।")
        return

    status_res = send_message(chat_id, "🔍 लिंक को प्रोसेस किया जा रहा है... कृपया प्रतीक्षा करें।", reply_to_message_id=msg_id)
    status_id = status_res.get("result", {}).get("message_id")

    episodes_list, title = get_kuku_all_episodes(text)
    if not episodes_list:
        edit_message(chat_id, status_id, "❌ वीडियो पार्ट्स निकालने में विफल। लिंक पुराना है या सुरक्षित है।")
        return

    total_parts = len(episodes_list)
    edit_message(chat_id, status_id, f"📥 कुल {total_parts} पार्ट्स मिले। डाउनलोडिंग शुरू की जा रही है...")

    downloaded_files = []
    for index, media_url in enumerate(episodes_list):
        edit_message(chat_id, status_id, f"📥 डाउनलोड हो रहा है... पार्ट: {index + 1}/{total_parts}")
        part_filename = f"part_{index}.mp4"
        try:
            with requests.get(media_url, stream=True) as r:
                r.raise_for_status()
                with open(part_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            downloaded_files.append(part_filename)
        except Exception as e:
            edit_message(chat_id, status_id, f"❌ पार्ट {index + 1} डाउनलोड करने में एरर आया: {str(e)}")
            for f in downloaded_files:
                if os.path.exists(f): os.remove(f)
            return

    edit_message(chat_id, status_id, "🎬 सभी पार्ट्स को जोड़कर एक फुल वीडियो बनाया जा रहा है (Merging)...")
    final_output = f"{title}_Full.mp4"
    merge_success = merge_videos(downloaded_files, final_output)

    for f in downloaded_files:
        if os.path.exists(f): os.remove(f)

    if not merge_success or not os.path.exists(final_output):
        edit_message(chat_id, status_id, "❌ वीडियो मर्ज करने में तकनीकी खराबी आई।")
        return

    edit_message(chat_id, status_id, "☁️ फुल वीडियो को आपके Supabase क्लाउड पर अपलोड किया जा रहा है...")
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{final_output}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY}

    try:
        with open(final_output, 'rb') as f:
            res = requests.post(upload_url, headers=headers, files={'file': f})
        if res.status_code == 200:
            final_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{final_output}"
            edit_message(chat_id, status_id, f"✅ **फुल वीडियो सफलतापूर्वक तैयार है!**\n\n🎬 **शो का नाम:** {title}\n📦 **कुल जोड़े गए पार्ट्स:** {total_parts}\n\n🔗 [यहाँ क्लिक करके फुल वीडियो डाउनलोड करें]({final_url})")
        else:
            edit_message(chat_id, status_id, f"❌ क्लाउड अपलोड फेल हुआ: {res.text}")
    except Exception as e:
        edit_message(chat_id, status_id, f"❌ अपलोड एरर: {str(e)}")
    finally:
        if os.path.exists(final_output):
            os.remove(final_output)

def main():
    print("बोट सफलतापूर्वक चालू हो गया है...")
    offset = 0
    while True:
        try:
            url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=20"
            res = requests.get(url, timeout=25).json()
            if "result" in res:
                for update in res["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update:
                        handle_bot_logic(update["message"])
        except Exception as e:
            print(f"Loop Error: {e}")
        time.sleep(1)

if __name__ == "__main__":
    main()
                
