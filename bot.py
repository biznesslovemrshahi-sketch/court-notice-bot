import os, json
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not BOT_TOKEN:
    raise SystemExit("TELEGRAM_BOT_TOKEN secret सेट गरिएको छैन")
CHAT_ID = "6887445420"

# सही सूचना पृष्ठहरू (पुराना /cp/notices, specialcourt.gov.np, phtc.p5.gov.np ठेगाना खुल्दैनथे)
COURTS = {
    "सर्वोच्च अदालत": "https://supremecourt.gov.np/web/anyanotice",
    "विशेष अदालत": "https://supremecourt.gov.np/court/specialcourt",
    "उच्च अदालत पाटन": "https://supremecourt.gov.np/court/patanhc",
    "प्रशासकीय अदालत": "https://admincourt.gov.np/",
    "राजस्व न्यायाधिकरण": "https://revenuetribunal.gov.np/",
}

DOC_HINTS = (".pdf", ".jpg", ".jpeg", ".png", ".doc", "/media/", "/uploads/", "notice", "suchana", "news")


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    # parse_mode हटाइयो: Markdown ले URL मा भएका _ जस्ता चिह्न बिगार्थ्यो
    r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg[:4000], "disable_web_page_preview": True}, timeout=30)
    print("telegram:", r.status_code)


def notices(page_url):
    r = requests.get(page_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    if r.status_code != 200 or "Request Rejected" in r.text[:500]:
        raise RuntimeError(f"blocked/err {r.status_code}")
    soup = BeautifulSoup(r.text, "html.parser")
    out = {}
    for a in soup.find_all("a", href=True):
        title = " ".join(a.get_text(" ", strip=True).split())
        href = a["href"].strip()
        if len(title) < 12 or href.startswith(("#", "javascript", "mailto", "tel")):
            continue
        full = urljoin(page_url, href)
        if any(h in full.lower() for h in DOC_HINTS):
            out[full] = title
    if not out:
        raise RuntimeError("no notice links found")
    return out


def check():
    try:
        with open("last.json") as f:
            old = json.load(f)
    except Exception:
        old = {}
    for name, page in COURTS.items():
        try:
            cur = notices(page)
        except Exception as e:
            print(f"{name}: skip ({e})")
            continue
        prev = old.get(name)
        if not isinstance(prev, dict):  # पहिलो पटक वा पुरानो hash ढाँचा: चुपचाप आधार बनाउने
            old[name] = {"seen": sorted(cur)}
            print(f"{name}: baseline {len(cur)}")
            continue
        seen = set(prev.get("seen", []))
        new = [(u, t) for u, t in cur.items() if u not in seen]
        if new:
            lines = [f"🔔 {name} मा नयाँ सूचना ({len(new)})", ""]
            for u, t in new[:10]:
                lines += [f"• {t}", u, ""]
            lines.append(f"सूचना पृष्ठ: {page}")
            send_telegram("\n".join(lines))
        prev["seen"] = sorted(seen | set(cur))[-1000:]
        print(f"{name}: {len(new)} new")
    with open("last.json", "w") as f:
        json.dump(old, f, ensure_ascii=False, indent=1)


check()
