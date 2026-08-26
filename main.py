import os
import threading
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask

# ==================== आपका नया टेलीग्राम टोकन ====================
TELEGRAM_BOT_TOKEN = "8804075824:AAEHnQj204iB7XAgzTxRbDmCk5gEdiqff5I"
# ====================================================================

app = Flask(__name__)

@app.route('/')
def home():
    return "MicroTV Automatic Downloader Bot is Running Perfect!"

# टेलीग्राम पर रिप्लाई भेजने का ऑटोमैटिक फंक्शन
def send_reply(chat_id, text):
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

# KukuTV से ड्रामा का नाम (Title) निकालना
def extract_drama_name(kuku_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(kuku_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.text.replace("on Kuku TV", "").strip() if soup.title else ""
            return title
    except Exception as e:
        print(f"Error fetching KukuTV page: {e}")
    return None

# MicroTV पर जाकर ड्रामा का डाउनलोड लिंक ढूंढना
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
            for link in links:
                href = link.get('href')
                text = link.text.strip().lower()
                # अगर ड्रामा का नाम वेबसाइट के किसी लिंक टेक्स्ट से मैच होता है
                if href and drama_name.lower() in text:
                    return href if href.startswith("http") else f"{microtv_url.rstrip('/')}/{href.lstrip('/')}"
    except Exception as e:
        print(f"Error searching on MicroTV: {e}")
    return None

# टेलीग्राम से मैसेज ऑटो-रीड करने वाला मेन वर्कर
def telegram_polling_worker():
    offset = None
    
    # पुराना कोई अटका हुआ वेबहुक हटाना ताकि नया टोकन सही से काम करे
    try:
        requests.get(f"https://telegram.org{TELEGRAM_BOT_TOKEN}/deleteWebhook")
        print("[INFO] Webhook cleared for new token.")
    except:
        pass

    print("[BOT] टेलीग्राम से मैसेज चेक करना शुरू कर रहा है...")
    
    while True:
        try:
            bot_url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {"timeout": 20, "offset": offset}
            response = requests.get(bot_url, params=params, timeout=25).json()
            
            if "result" in response:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        user_message = update["message"]["text"].strip()
                        user_chat_id = update["message"]["chat"]["id"] 
                        
                        # 1. जब कोई यूजर /start भेजता है
                        if user_message == "/start":
                            welcome_msg = (
                                "👋 <b>नमस्ते! आपका नया ऑटोमैटिक बॉट पूरी तरह एक्टिव है।</b>\n\n"
                                "मुझे किसी भी KukuTV ड्रामा का लिंक भेजें, मैं उसका डाउनलोड लिंक ढूंढ कर दूंगा।"
                            )
                            send_reply(user_chat_id, welcome_msg)
                        
                        # 2. जब कोई यूजर KukuTV का लिंक भेजता है
                        elif "kukutv" in user_message or "kuku.tv" in user_message:
                            send_reply(user_chat_id, "🔄 <b>लिंक मिल गया है! कूकू टीवी से ड्रामा की डिटेल्स निकाली जा रही हैं, कृपया रुकें...</b>")
                            
                            drama_title = extract_drama_name(user_message)
                            if drama_title:
                                send_reply(user_chat_id, f"🔍 <b>ड्रामा नाम मिला:</b> {drama_title}\nअब MicroTV पर डायरेक्ट डाउनलोड लिंक ढूंढा जा रहा है...")
                                direct_link = search_microtv_source(drama_title)
                                
                                if direct_link:
                                    success_msg = f"✅ <b>सफलतापूर्वक लिंक मिल गया!</b>\n\n🎬 <b>कूकू ड्रामा:</b> {drama_title}\n📥 <a href='{direct_link}'>यहाँ क्लिक करके डायरेक्ट डाउनलोड करें</a>"
                                    send_reply(user_chat_id, success_msg)
                                else:
                                    fallback_url = f"http://microtv.one{drama_title.replace(' ', '+')}"
                                    send_reply(user_chat_id, f"⚠️ डायरेक्ट लिंक नहीं मिला। आप यहाँ चेक कर सकते हैं: {fallback_url}")
                            else:
                                send_reply(user_chat_id, "❌ कूकू टीवी लिंक से ड्राma की जानकारी नहीं निकाली जा सकी।")
                                
        except Exception as e:
            print(f"Polling error: {e}")
        time.sleep(1)

if __name__ == "__main__":
    # पोलिंग को बैकग्राउंड थ्रेड में शुरू करें
    threading.Thread(target=telegram_polling_worker, daemon=True).start()
    
    # Render के लिए वेब सर्वर चालू करें
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
