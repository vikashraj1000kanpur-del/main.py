import os
import threading
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask, request

# ==================== अपना टेलीग्राम डेटा यहाँ डालें ====================
TELEGRAM_BOT_TOKEN = "8804075824:AAGATUZhpndkYtD67doTp7QfUIxFq0ZVn-Y"
TELEGRAM_CHAT_ID = "8529632128"
# ====================================================================

app = Flask(__name__)

@app.route('/')
def home():
    return "KukuTV to MicroTV Downloader Bot is Running!"

# कूकू टीवी लिंक से ड्रामा का नाम या आईडी खोजने का फंक्शन
def extract_drama_name(kuku_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(kuku_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # कूकू टीवी पेज से ड्रामा का टाइटल (नाम) निकालना
            title = soup.title.text.replace("on Kuku TV", "").strip() if soup.title else ""
            return title
    except Exception as e:
        print(f"Error fetching KukuTV page: {e}")
    return None

# MicroTV वेबसाइट पर जाकर डाउनलोड लिंक या वीडियो सोर्स खोजना
def search_microtv_source(drama_name):
    if not drama_name:
        return None
    
    microtv_url = "http://microtv.one"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(microtv_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a')
            
            # ड्रामा के नाम से मैच खाता हुआ लिंक वेबसाइट पर ढूंढना
            for link in links:
                href = link.get('href')
                text = link.text.strip().lower()
                
                if href and drama_name.lower() in text:
                    full_download_url = href if href.startswith("http") else f"{microtv_url.rstrip('/')}/{href.lstrip('/')}"
                    return full_download_url
    except Exception as e:
        print(f"Error searching on MicroTV: {e}")
    return None

# टेलीग्राम पर रिप्लाई (मैसेज) भेजने का फंक्शन
def send_reply(chat_id, text):
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

# टेलीग्राम से आने वाले नए मैसेजेस को चेक करने का लूप (Long Polling)
def telegram_bot_listener():
    offset = None
    bot_url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    print("[BOT] टेलीग्राम यूजर के मैसेज का इंतजार कर रहा है...")
    
    while True:
        try:
            params = {"timeout": 30, "offset": offset}
            response = requests.get(bot_url, params=params, timeout=35).json()
            
            if "result" in response:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        user_message = update["message"]["text"].strip()
                        user_chat_id = update["message"]["chat"]["id"]
                        
                        # चेक करें कि क्या यूजर ने KukuTV का लिंक भेजा है
                        if "kukutv.app" in user_message or "kuku.tv" in user_message:
                            send_reply(user_chat_id, "🔄 <b>लिंक मिल गया है! कूकू टीवी से ड्रामा की डिटेल्स निकाली जा रही हैं, कृपया रुकें...</b>")
                            
                            # 1. कूकू टीवी से ड्रामा का नाम निकालें
                            drama_title = extract_drama_name(user_message)
                            
                            if drama_title:
                                send_reply(user_chat_id, f"🔍 <b>ड्रामा का नाम मिला:</b> {drama_title}\nअब MicroTV पर इसका डायरेक्ट डाउनलोड लिंक ढूंढा जा रहा है...")
                                
                                # 2. MicroTV पर जाकर उसका डाउनलोड सोर्स लिंक ढूंढें
                                direct_link = search_microtv_source(drama_title)
                                
                                if direct_link:
                                    success_msg = f"✅ <b>सफलतापूर्वक लिंक मिल गया!</b>\n\n🎬 <b>ड्रामा:</b> {drama_title}\n📥 <a href='{direct_link}'>यहाँ क्लिक करके डायरेक्ट डाउनलोड करें</a>"
                                    send_reply(user_chat_id, success_msg)
                                else:
                                    # अगर नाम से नहीं मिला, तो एक अनुमानित बैकअप लिंक दे दें
                                    fallback_url = f"http://microtv.one{drama_title.replace(' ', '+')}"
                                    send_reply(user_chat_id, f"⚠️ इस ड्रामा का डायरेक्ट लिंक नहीं मिल पाया। आप यहाँ चेक कर सकते हैं: {fallback_url}")
                            else:
                                send_reply(user_chat_id, "❌ कूकू टीवी लिंक से ड्रामा की जानकारी नहीं निकाली जा सकी। कृपया सही लिंक भेजें।")
                                
        except Exception as e:
            print(f"Error in listener loop: {e}")
        time.sleep(1)

if __name__ == "__main__":
    # बॉट लिसनर को अलग थ्रेड में चालू करें
    threading.Thread(target=telegram_bot_listener, daemon=True).start()
    
    # Render के लिए वेब सर्वर चालू करें
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
