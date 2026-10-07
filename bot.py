import requests, hashlib, json
from bs4 import BeautifulSoup
from datetime import datetime

BOT_TOKEN = "8953619881:AAE88e-Vec7s8irvSRXSfB98ptp2zRXA1SA"
CHAT_ID = "6887445420"

COURTS = {
    "सर्वोच्च अदालत": "https://supremecourt.gov.np/cp/notices",
    "विशेष अदालत": "https://specialcourt.gov.np/en/notices",
    "उच्च अदालत पाटन": "https://phtc.p5.gov.np/en/notices-and-announcements",
    "प्रशासनिक अदालत": "https://supremecourt.gov.np/web/ac/notices",
    "राजस्व न्यायाधिकरण": "https://supremecourt.gov.np/web/rt-kathmandu/notices"
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def check():
    try:
        with open("last.json","r") as f: old=json.load(f)
    except: old={}

    for name, link in COURTS.items():
        try:
            r = requests.get(link, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
            soup = BeautifulSoup(r.text, 'html.parser')
            text = soup.get_text(" ", strip=True)[:4000]
            h = hashlib.md5(text.encode()).hexdigest()
            if name not in old:
                old[name]=h
            elif old[name]!=h:
                send_telegram(f"🔔 *{name} मा नयाँ सूचना!*\n\n🔗 {link}\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                old[name]=h
        except Exception as e:
            print(e)
    with open("last.json","w") as f: json.dump(old,f)

check()
