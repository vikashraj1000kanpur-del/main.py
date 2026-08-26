import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

# ==================== अपना टेलीग्राम डेटा यहाँ डालें ====================
TELEGRAM_BOT_TOKEN = "8804075824:AAGATUZhpndkYtD67doTp7QfUIxFq0ZVn-Y"
TELEGRAM_CHAT_ID = "8529632128"
# ====================================================================

app = Flask(__name__)

# टेलीग्राम पर रिप्लाई (मैसेज) भेजने का फंक्शन
def send_reply(chat_id, text):
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

# KukuTV लिंक से ड्रामा का नाम निकालने का फंक्शन
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

# MicroTV वेबसाइट पर जाकर डाउनलोड लिंक खोजना
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
                if href and drama_name.lower() in text:
                    return href if href.startswith("http") else f"{microtv_url.rstrip('/')}/{href.lstrip('/')}"
    except Exception as e:
        print(f"Error searching on MicroTV: {e}")
    return None

@app.route('/')
def home():
    return "Bot Server is Alive!"

# टेलीग्राम इस URL पर आपके बॉट के मैसेजेस भेजेगा
@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def telegram_webhook():
    update = request.get_json()
    
    if "message" in update and "text" in update["message"]:
        user_message = update["message"]["text"].strip()
        user_chat_id = update["message"]["chat"]["id"]
        
        # 1. अगर यूजर /start भेजता है
        if user_message == "/start":
            send_reply(user_chat_id, "👋 <b>नमस्ते!</b> मुझे किसी भी KukuTV ड्राma का लिंक भेजें, मैं उसका डाउनलोड लिंक ढूंढ कर दूंगा।")
        
        # 2. अगर यूजर KukuTV का लिंक भेजता है
        elif "kukutv" in user_message or "kuku.tv" in user_message:
            send_reply(user_chat_id, "🔄 <b>लिंक मिल गया है! कूकू टीवी से डिटेल्स निकाली जा रही हैं, कृपया रुकें...</b>")
            
            drama_title = extract_drama_name(user_message)
            if drama_title:
                send_reply(user_chat_id, f"🔍 <b>ड्रामा नाम:</b> {drama_title}\nअब MicroTV पर डायरेक्ट लिंक ढूंढा जा रहा है...")
                direct_link = search_microtv_source(drama_title)
                
                if direct_link:
                    success_msg = f"✅ <b>सफलतापूर्वक लिंक मिल गया!</b>\n\n🎬 <b>ड्रामा:</b> {drama_title}\n📥 <a href='{direct_link}'>यहाँ क्लिक करके डायरेक्ट डाउनलोड करें</a>"
                    send_reply(user_chat_id, success_msg)
                else:
                    fallback_url = f"http://microtv.one{drama_title.replace(' ', '+')}"
                    send_reply(user_chat_id, f"⚠️ डायरेक्ट लिंक नहीं मिला। आप यहाँ मैन्युअली चेक कर सकते हैं: {fallback_url}")
            else:
                send_reply(user_chat_id, "❌ कूकू टीवी लिंक से ड्रामा की जानकारी नहीं निकाली जा सकी।")
                
    return jsonify({"status": "success"}), 200

# वेबहुक को ऑटोमैटिक टेलीग्राम से कनेक्ट करने का लॉजिक
def set_webhook():
    # Render का अपना URL निकालें
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        webhook_url = f"{render_url.rstrip('/')}/{TELEGRAM_BOT_TOKEN}"
        tg_url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}"
        requests.get(tg_url)
        print(f"[INFO] Webhook successfully set to: {webhook_url}")

# सर्वर शुरू होने पर वेबहुक सेट करें
with app.app_context():
    try:
        set_webhook()
    except Exception as e:
        print(f"Error setting webhook: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
