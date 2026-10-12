import os
import re
import requests
import telebot
from telebot import apihelper

# --- ضبط بروكسي PythonAnywhere لتفادي خطأ 503 ---
proxy_url = "http://proxy.server:3128"
os.environ['HTTP_PROXY'] = proxy_url
os.environ['HTTPS_PROXY'] = proxy_url
apihelper.proxy = {'https': proxy_url}

TELEGRAM_BOT_TOKEN = "8839833163:AAHD4c9AzbPnQgOtb-iHmSyuE_XmlP4glVY"
URLSCAN_API_KEY = "019fade6-6a73-7770-afcf-9041943cdad7"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# قائمة بالنطاقات الآمنة الشائعة للرد الفوري
SAFE_DOMAINS = [
    'youtube.com', 'youtu.be', 'google.com', 'facebook.com',
    'instagram.com', 'twitter.com', 'x.com', 'tiktok.com', 'telegram.org'
]

def extract_url(text):
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    return urls[0] if urls else None

def fast_check_url(target_url):
    domain = target_url.split("//")[-1].split("/")[0].lower()

    # 1. استجابة فورية للروابط المعروفة
    for safe in SAFE_DOMAINS:
        if safe in domain:
            return f"✅ موقع معروف وآمن!\n🌐 الدومين: {domain}"

    # 2. كشف فوري للامتدادات المشبوهة
    suspicious_exts = ['.buzz', '.top', '.xyz', '.site', '.online', '.club']
    if any(domain.endswith(ext) for ext in suspicious_exts):
        return (
            f"🚨 تحذير! رابط مشبوه جداً (دومين احتيالي)!\n\n"
            f"🌐 الدومين: {domain}\n"
            f"⚠️ التقييم: خطر عالي (100%)\n"
            f"🚫 تنبيه: لا تقم بفتح الرابط أو إدخال أي بيانات."
        )

    # 3. بحث سريع عبر API مع ضبط البروكسي
    search_endpoint = f"https://urlscan.io/api/v1/search/?q=domain:{domain}"
    headers = {'API-Key': URLSCAN_API_KEY}
    proxies = {'http': proxy_url, 'https': proxy_url}

    try:
        res = requests.get(search_endpoint, headers=headers, proxies=proxies, timeout=5)
        if res.status_code == 200:
            results = res.json().get('results', [])
            if results:
                verdicts = results[0].get('verdicts', {}).get('overall', {})
                malicious = verdicts.get('malicious', False)
                score = verdicts.get('score', 0)

                if malicious or score > 0:
                    return (
                        f"🚨 تحذير! الرابط غير آمن!\n\n"
                        f"🌐 الدومين: {domain}\n"
                        f"⚠️ نسبة الخطر: {score}%\n"
                        f"🚫 تنبيه: تجنب التعامل مع هذا الموقع."
                    )
                else:
                    return (
                        f"✅ الرابط يبدو آمناً!\n\n"
                        f"🌐 الدومين: {domain}\n"
                        f"📊 نسبة الخطر: 0%"
                    )
    except Exception:
        pass

    return (
        f"⚠️ رابط جديد أو غير مسجل سابقاً\n\n"
        f"🌐 الدومين: {domain}\n"
        f"👉 ينصح بالحذر عند التعامل مع هذا الرابط."
    )

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! 👋\nأرسل لي أي رابط وسأقوم بفحصه فوراً.")

@bot.message_handler(func=lambda msg: msg.text and ("http://" in msg.text or "https://" in msg.text))
def handle_url(message):
    clean_url = extract_url(message.text)
    if clean_url:
        result = fast_check_url(clean_url)
        bot.reply_to(message, result, parse_mode="Markdown")

# إعادة المحاولة التلقائية عند انقطاع البروكسي
bot.infinity_polling(timeout=10, long_polling_timeout=5)