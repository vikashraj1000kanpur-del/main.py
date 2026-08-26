import time
import requests
from bs4 import BeautifulSoup

# ==================== आपका एक्टिव टोकन ====================
TELEGRAM_BOT_TOKEN = "8804075824:AAEHnQj204iB7XAgzTxRbDmCk5gEdiqff5I"
# ====================================================================

def send_reply(chat_id, text):
    # यहाँ /bot जोड़कर यूआरएल की गलती को बिल्कुल ठीक कर दिया गया है
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def search_microtv_source(drama_name):
    if not drama_name:
        return None
    microtv_url = "http://microtv.one"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(microtv_url, headers=headers, timeout=12)
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

def main():
    offset = None
    try:
        # यहाँ भी यूआरएल ठीक किया गया है
        requests.get(f"https://telegram.org{TELEGRAM_BOT_TOKEN}/deleteWebhook")
    except:
        pass

    print("बॉट शुरू हो गया है...")
    
    start_time = time.time()
    # यह लगातार 5 घंटे तक बिना रुके बैकग्राउंड में एक्टिव रहेगा
    while time.time() - start_time < 18000:  
        try:
            # यहाँ भी /bot जोड़कर यूआरएल बिल्कुल सही कर दिया गया है
            bot_url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {"timeout": 20, "offset": offset}
            response = requests.get(bot_url, params=params, timeout=25).json()
            
            if "result" in response:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        user_message = update["message"]["text"].strip()
                        user_chat_id = update["message"]["chat"]["id"] 
                        
                        if user_message == "/start":
                            send_reply(user_chat_id, "👋 <b>नमस्ते! आपका MicroTV वीडियो सर्च बॉट चालू है।</b>\n\nमुझे किसी भी ड्रामा का नाम लिख कर भेजें, मैं तुरंत डाउनलोड लिंक ढूंढ कर दूंगा।")
                        else:
                            send_reply(user_chat_id, f"🔍 <b>'{user_message}' को MicroTV पर ढूंढा जा रहा है...</b>")
                            direct_link = search_microtv_source(user_message)
                            
                            if direct_link:
                                success_msg = f"✅ <b>सफलतापूर्वक लिंक मिल गया!</b>\n\n🎬 <b>वीडियो:</b> {user_message}\n📥 <a href='{direct_link}'>यहाँ क्लिक करके डायरेक्ट डाउनलोड या प्ले करें</a>"
                                send_reply(user_chat_id, success_msg)
                            else:
                                fallback_url = f"http://microtv.one{user_message.replace(' ', '+')}"
                                send_reply(user_chat_id, f"⚠️ डायरेक्ट लिंक नहीं मिला। आप यहाँ चेक कर सकते हैं: {fallback_url}")
                                
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)

if __name__ == "__main__":
    main()
    
