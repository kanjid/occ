# automate.py


import json
from datetime import datetime
from telethon import TelegramClient, events, utils

# ========== CONFIGURE ==========
API_ID = <ESCRIBE AQUÍ TU API_ID>
API_HASH = <"ESCRIBE AQUÍ TU API_HASH">
SESSION = "my_session"

# Target: can be @handle (string) or -100... id (integer)
TARGET = -1003058429703

# Keywords to match (case-insensitive)
CLAVES = ["hack", "vpn", "exploit"]

# Output file (JSON Lines: one JSON object per line)
ALERTS_FILE = "alerts.jsonl"
# ===============================

client = TelegramClient(SESSION, API_ID, API_HASH)


async def main():
    await client.start()
    # Preload dialogs so get_entity with id works reliably
    await client.get_dialogs()

    destino = await client.get_entity(TARGET)
    nombre = getattr(destino, "title", getattr(destino, "username", str(destino)))
    objetivo_id = utils.get_peer_id(destino)
    print(f"🔎 Monitoring Channel: {nombre} (chat_id={objetivo_id})")

    @client.on(events.NewMessage(chats=destino))
    async def handler(event):
        # raw_text includes captions for media and strips formatting
        texto = (event.raw_text or "").strip()
        preview = texto[:200]  # preview length for console

        # Print a concise preview to console (avoids flooding)
        print(f"📡 New msg in {event.chat_id} (msg {event.id}) - preview: {preview!r}")

        # Check for any keyword matches (case-insensitive)
        lower_text = texto.lower()
        matched = [p for p in CLAVES if p in lower_text]
        if matched:
            alerta = {
                "ts": datetime.utcnow().isoformat() + "Z",
                "chat_id": event.chat_id,
                "msg_id": event.id,
                "chat_title": nombre,
                "sender_id": getattr(event.message.sender, "id", None),
                "sender_username": getattr(event.message.sender, "username", None),
                "texto_full": texto,
                "preview": preview,
                "matched_keys": matched,
            }

            # Console notification (concise)
            print("🚨 ALERT matched:", alerta["matched_keys"], "— preview:", preview)

            # Append the full alert JSON to the JSONL file
            with open(ALERTS_FILE, "a", encoding="utf-8") as fh:
                json.dump(alerta, fh, ensure_ascii=False)
                fh.write("\n")

    print("🤖 Tracking... (Ctrl+C para detener)")
    await client.run_until_disconnected()


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Interrupt by user")
