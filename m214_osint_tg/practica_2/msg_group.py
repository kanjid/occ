
# archivo: group_msgs.py
# ==============================================


from telethon import TelegramClient, utils
import json
import re
from datetime import datetime

# ========= CONFIGURA TUS CREDENCIALES =========
api_id = <ESCRIBE AQUÍ TU API_ID>
api_hash = <"ESCRIBE AQUÍ TU API_HASH">

# Puedes usar @handle público (recomendado si existe)
# TARGET = "@tu_canal_o_grupo"
# o un ID -100... como entero:
TARGET = -1002355478671

# Número de mensajes a descargar
LIMIT = 200

# Archivo de salida
OUTPUT_FILE = "msgs_data.json"

# ==============================================

URL_RE = re.compile(r'https?://\S+', re.IGNORECASE)


def classify_media(msg) -> str | None:
    """
    Detecta el tipo de contenido multimedia (foto, video, sticker, audio, etc.)
    """
    if not msg.media:
        return None

    if getattr(msg, "photo", None):
        return "photo"

    # Web preview (cuando hay link con vista enriquecida)
    if getattr(msg.media, "webpage", None):
        return "webpage"

    doc = getattr(msg, "document", None)
    if doc:
        mime = (getattr(doc, "mime_type", "") or "").lower()
        attrs = getattr(doc, "attributes", []) or []

        # ¿Sticker?
        if any(getattr(a, "__class__", type("X", (), {})).__name__ == "DocumentAttributeSticker" for a in attrs):
            return "sticker"

        # ¿GIF?
        if "gif" in mime:
            return "gif"

        # ¿Audio o voice note?
        if mime.startswith("audio/"):
            if any(
                getattr(a, "__class__", type("X", (), {})).__name__ == "DocumentAttributeAudio"
                and getattr(a, "voice", False)
                for a in attrs
            ):
                return "voice"
            return "audio"

        # ¿Video?
        if mime.startswith("video/"):
            return "video"

        return "document"

    return "unknown"


def build_summary(item: dict) -> str:
    """Devuelve una descripción breve según el tipo de mensaje."""
    t = item.get("type")
    mt = item.get("media_type")

    if t == "service":
        return f"📢 service: {item.get('service_action') or 'event'}"
    if t == "text":
        return "💬 text"
    if t == "media":
        icon = {
            "photo": "📷",
            "video": "🎞️",
            "audio": "🎵",
            "voice": "🎙️",
            "gif": "🖼️",
            "sticker": "🔖",
            "document": "📎",
            "webpage": "🌐",
            "unknown": "❓",
        }.get(mt or "unknown", "❓")
        return f"{icon} {mt or 'media'}"
    return "🗂️ other"


async def main():
    client = TelegramClient("my_session", API_ID, API_HASH)
    await client.start()
    await client.get_dialogs()  # carga la caché

    destino = await client.get_entity(TARGET)
    nombre = getattr(destino, "title", getattr(destino, "username", str(destino)))
    peer_id = utils.get_peer_id(destino)
    print(f"🔎 Extrayendo de: {nombre} (chat_id={peer_id}) | limit={LIMIT}")

    mensajes = await client.get_messages(destino, limit=LIMIT)
    print(f"📥 Mensajes recibidos: {len(mensajes)}")

    out = []
    for m in mensajes:
        # Detección universal de mensajes de servicio
        is_service = hasattr(m, "action") and m.action is not None
        txt = (m.raw_text or "")
        links = URL_RE.findall(txt)

        # Extraer URLs en botones inline (si existen)
        buttons_urls = []
        if m.buttons:
            for row in m.buttons:
                for b in row:
                    url = getattr(b, "url", None)
                    if url:
                        buttons_urls.append(url)

        media_type = classify_media(m) if m.media else None

        item = {
            "id": m.id,
            "date": m.date.isoformat() if m.date else None,
            "texto": txt,
            "type": (
                "service"
                if is_service
                else ("media" if m.media and not txt else ("text" if txt else "other"))
            ),
            "has_media": bool(m.media),
            "media_type": media_type,
            "service_action": type(m.action).__name__ if is_service and m.action else None,
            "links": links or None,
            "buttons_urls": buttons_urls or None,
            "reply_to": getattr(m, "reply_to_msg_id", None),
            "forward_from": getattr(getattr(m, "forward", None), "from_name", None),
            "views": getattr(m, "views", None),
            "forwards": getattr(m, "forwards", None),
        }
        item["summary"] = build_summary(item)
        out.append(item)

    # Guardar JSON enriquecido
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"✅ Guardado: {OUTPUT_FILE} ({len(out)} registros)")

    # Conteo rápido por tipo
    tipos = {}
    for i in out:
        t = i.get("type") or "other"
        tipos[t] = tipos.get(t, 0) + 1
    print("📊 Tipos:", tipos)

    await client.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
