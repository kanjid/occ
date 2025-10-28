# pip install telethon email-validator phonenumbers urlextract tldextract
from telethon import TelegramClient, events
from telethon.tl import types
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from urlextract import URLExtract
import tldextract

API_ID = <Aquí tu api_id>
API_HASH = <"Aquí tu api_hash"
CHANNELS = ["@Aquí channel_como handler"] #<--- Recuerda este detalle

extractor = URLExtract()

def find_emails(words):
    emails = []
    for w in words:
        try:
            v = validate_email(w, check_deliverability=False)
            emails.append(v.normalized)
        except EmailNotValidError:
            pass
    return list(dict.fromkeys(emails))

def find_phones(text, region="ES"):
    phones = []
    for m in phonenumbers.PhoneNumberMatcher(text, region):
        phones.append(phonenumbers.format_number(m.number, phonenumbers.PhoneNumberFormat.E164))
    return list(dict.fromkeys(phones))

def find_urls_and_domains(text):
    urls = extractor.find_urls(text)
    domains = []
    for u in urls:
        ext = tldextract.extract(u)
        if ext.registered_domain:
            domains.append(ext.registered_domain)
    return list(dict.fromkeys(urls)), list(dict.fromkeys(domains))

client = TelegramClient("leaks_session", API_ID, API_HASH)

@client.on(events.NewMessage(chats=CHANNELS))
async def handler(event):
    msg = event.message
    text = (msg.raw_text or "").strip()
    words = text.replace("\n", " ").split()

    # 1) Entidades nativas de Telegram (sin regex)
    mentions = []
    urls_from_entities = []
    if msg.entities:
        for ent in msg.entities:
            if isinstance(ent, types.MessageEntityMention):  # @usuario
                # recorta el trozo del texto que ocupa la entidad
                mentions.append(text[ent.offset: ent.offset + ent.length])
            if isinstance(ent, (types.MessageEntityUrl, types.MessageEntityTextUrl)):
                # para TextUrl la URL va en ent.url
                if hasattr(ent, "url") and ent.url:
                    urls_from_entities.append(ent.url)

    # 2) Validadores “inteligentes”
    emails = find_emails(words)
    phones = find_phones(text)
    urls, domains = find_urls_and_domains(text)
    urls = list(dict.fromkeys(urls + urls_from_entities))

    if emails or phones or urls or mentions:
        print({
            "channel": event.chat.username if event.chat else "",
            "message_id": msg.id,
            "emails": emails,
            "phones": phones,
            "urls": urls,
            "domains": domains,
            "mentions": mentions,
            "snippet": text[:180].replace("\n", " ")
        })

client.start()
client.run_until_disconnected()





# pip install telethon tldextract
import asyncio
import csv
import os
from datetime import datetime
from telethon import TelegramClient
from telethon.tl import types
import tldextract

# ========= Config =========
API_ID = int(os.getenv("TG_API_ID", "27914351"))        # <-- pon tu API_ID o setea env
API_HASH = os.getenv("TG_API_HASH", "29688de6a5a48c5e681f2ef6ad218a05")    # <-- pon tu API_HASH o setea env

# Canales públicos (username del canal sin @)
CHANNELS = [
    "@CanalRed_TV"
]

# Mensajes por canal (sube/baja según tiempo disponible)
LIMIT_PER_CHANNEL = int(os.getenv("LIMIT_PER_CHANNEL", "200"))

# Salida
OUT_CSV = os.getenv("OUT_CSV", f"telegram_snapshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv")

# ========= Heurísticas ultra-rápidas =========

# Evita que tldextract haga fetch de la PSL online
tldx = tldextract.TLDExtract(suffix_list_urls=None)

def fast_email_candidates(words):
    """
    Heurística SIN validadores lentos:
    - Contiene '@' y '.'
    - Local (antes de @) 1..64, dominio 3..255
    - Dominio con TLD de 2..10
    """
    emails = []
    seen = set()
    for w in words:
        w = w.strip(".,;:()[]{}<>\"'").lower()
        if "@" not in w or "." not in w or " " in w:
            continue
        if w.count("@") != 1:
            continue
        local, dom = w.split("@", 1)
        if not (1 <= len(local) <= 64 and 3 <= len(dom) <= 255):
            continue
        ext = tldx(dom)
        if not ext.registered_domain or not ext.suffix or not (2 <= len(ext.suffix) <= 10):
            continue
        if w not in seen:
            seen.add(w)
            emails.append(w)
    return emails

def fast_domains_from_text(words):
    """
    Heurística de dominio:
    - contiene '.'
    - tldextract con PSL local
    """
    domains = []
    seen = set()
    for w in words:
        w = w.strip(".,;:()[]{}<>\"'").lower()
        if "." not in w:
            continue
        # evita tokens claramente no-dominios
        if w.startswith("http://") or w.startswith("https://"):
            # si viene como URL, recorta dominio con tldextract
            ext = tldx(w)
        else:
            ext = tldx(w)
        rd = ext.registered_domain
        if rd and rd not in seen:
            seen.add(rd)
            domains.append(rd)
    return domains

def fast_urls_from_entities(msg, text):
    urls = []
    if msg.entities:
        for ent in msg.entities:
            if isinstance(ent, (types.MessageEntityUrl, types.MessageEntityTextUrl)):
                if hasattr(ent, "url") and ent.url:
                    urls.append(ent.url)
                else:
                    # cortar trozo de texto si es MessageEntityUrl
                    urls.append(text[ent.offset: ent.offset + ent.length])
    # dedup básica
    out = []
    seen = set()
    for u in urls:
        u = u.strip()
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out

def fast_mentions_from_entities(msg, text):
    mentions = []
    if msg.entities:
        for ent in msg.entities:
            if isinstance(ent, types.MessageEntityMention):
                mentions.append(text[ent.offset: ent.offset + ent.length])
    # dedup
    out, seen = [], set()
    for m in mentions:
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out

def fast_phones(text):
    """
    Heurística rápida (sin phonenumbers):
    - Busca tokens con + y 8..15 dígitos totales
    - O tokens de 9..11 dígitos si son 'compactos'
    Suficiente para clase; evita coste alto de 'phonenumbers'.
    """
    phones = []
    seen = set()
    for raw in text.replace("\n", " ").split():
        w = raw.strip(".,;:()[]{}<>\"'")
        digits = "".join(ch for ch in w if ch.isdigit())
        if w.startswith("+") and 8 <= len(digits) <= 15:
            if w not in seen:
                seen.add(w); phones.append(w)
        elif w.isdigit() and 9 <= len(w) <= 11:
            if w not in seen:
                seen.add(w); phones.append(w)
    return phones

# ========= Descarga rápida por canal =========

async def fetch_channel(client, channel_username, limit=200):
    out_rows = []
    try:
        async for msg in client.iter_messages(channel_username, limit=limit):
            if not msg or not msg.raw_text:
                continue
            text = msg.raw_text.strip()
            # Salta mensajes enormes para ganar velocidad
            if len(text) > 3000:
                continue

            words = text.replace("\n", " ").split()

            # Entidades: URLs y @mentions
            urls = fast_urls_from_entities(msg, text)
            mentions = fast_mentions_from_entities(msg, text)

            # Heurísticas rápidas (sin librerías pesadas)
            emails = fast_email_candidates(words)
            domains = fast_domains_from_text(words)
            phones = fast_phones(text)

            if not (emails or domains or phones or mentions or urls):
                continue

            out_rows.append({
                "channel": channel_username,
                "message_id": msg.id,
                "date_utc": msg.date.isoformat() if msg.date else "",
                "emails": ";".join(emails),
                "domains": ";".join(domains),
                "phones": ";".join(phones),
                "mentions": ";".join(mentions),
                "urls": ";".join(urls),
                "snippet": text[:180].replace("\n", " ")
            })
    except Exception as e:
        out_rows.append({
            "channel": channel_username,
            "message_id": "",
            "date_utc": "",
            "emails": "",
            "domains": "",
            "phones": "",
            "mentions": "",
            "urls": "",
            "snippet": f"[ERROR leyendo canal: {e}]"
        })
    return out_rows

async def main():
    async with TelegramClient("leaks_snapshot_session", API_ID, API_HASH) as client:
        # En paralelo por canal
        tasks = [fetch_channel(client, ch, LIMIT_PER_CHANNEL) for ch in CHANNELS]
        results = await asyncio.gather(*tasks)

        # Aplanar y guardar CSV
        rows = [r for sub in results for r in sub]
        if not rows:
            print("No se detectaron entidades con el límite actual.")
            return

        fieldnames = ["channel","message_id","date_utc","emails","domains","phones","mentions","urls","snippet"]
        with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fieldnames)
            w.writeheader()
            for row in rows:
                w.writerow(row)
        print(f"✅ CSV generado: {OUT_CSV}  | filas: {len(rows)}")

if __name__ == "__main__":
    asyncio.run(main())
