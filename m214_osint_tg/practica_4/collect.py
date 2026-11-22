# archivo: collect.py
# ===============================================

import os
import re
import json
from typing import List, Tuple

from telethon import TelegramClient
from telethon.errors import ChatAdminRequiredError, ChannelPrivateError

# ========= CONFIGURA TUS CREDENCIALES =========
API_ID = <ESCRIBE AQUÍ TU API_ID>
API_HASH = <"ESCRIBE AQUÍ TU API_HASH">
SESSION_NAME = "my_session"

# ID numérico del grupo/canal (⚠️ entero, NO string)
GROUP_ID = -1003452345454  # <-- pon aquí tu -100...

# Límite de mensajes a procesar
LIMIT = 200

# Carpeta de descargas
DOWNLOAD_DIR = "descargas"

# Archivo JSON de salida
OUTPUT_FILE = "info_grupo.json"
# ===============================================

URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)


def extract_urls(text: str) -> List[str]:
    return URL_RE.findall(text or "")


def entity_type_flags(entity) -> Tuple[bool, bool]:
    """
    Devuelve (is_megagroup, is_broadcast) para Channels.
    - is_megagroup: True si es supergrupo/megagrupo
    - is_broadcast: True si es canal tipo 'broadcast'
    Para Chats normales, ambos False.
    """
    is_mega = bool(getattr(entity, "megagroup", False))
    is_bcast = bool(getattr(entity, "broadcast", False))
    return is_mega, is_bcast


async def main():
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Resolver entidad por ID (entero)
    try:
        grupo = await client.get_entity(GROUP_ID)
    except ChannelPrivateError:
        print("❌ No puedes acceder a este chat/canal (privado o expulsado).")
        return

    title = getattr(grupo, "title", str(GROUP_ID))
    is_mega, is_bcast = entity_type_flags(grupo)
    print(f"📡 Destino: {title} | ID: {GROUP_ID} | megagroup={is_mega} | broadcast={is_bcast}")

    # Obtener mensajes
    mensajes = await client.get_messages(grupo, limit=LIMIT)
    print(f"📥 Mensajes obtenidos: {len(mensajes)}")

    enlaces = []
    for m in mensajes:
        # Extrae enlaces del texto/caption
        enlaces.extend(extract_urls(getattr(m, "text", "") or ""))

        # Descarga media si existe
        if m.media:
            await m.download_media(DOWNLOAD_DIR)

    # Intentar obtener participantes SOLO si es megagrupo
    usuarios = []
    usuarios_nota = None
    if is_mega:
        try:
            participantes = await client.get_participants(grupo)
            usuarios = [u.username for u in participantes if getattr(u, "username", None)]
        except ChatAdminRequiredError:
            usuarios_nota = "User list not accessible: admin privileges required in this megagroup."
        except Exception as e:
            usuarios_nota = f"Could not fetch participants: {type(e).__name__}: {e}"
    else:
        # Es un canal broadcast o un chat sin soporte de listado
        if is_bcast:
            usuarios_nota = "This is a broadcast channel. Subscriber list is not accessible unless you are an admin."
        else:
            usuarios_nota = "Participants listing is not supported for this chat type."

    # Quitar duplicados de enlaces
    enlaces_unicos = sorted(set(enlaces))

    data = {
        "group_title": title,
        "group_id": GROUP_ID,
        "is_megagroup": is_mega,
        "is_broadcast": is_bcast,
        "messages_collected": len(mensajes),
        "links": enlaces_unicos,
        "links_count": len(enlaces_unicos),
        "users": usuarios if usuarios else None,
        "users_count": len(usuarios) if usuarios else 0,
        "users_note": usuarios_nota,
        "download_dir": os.path.abspath(DOWNLOAD_DIR),
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"✅ Guardado: {OUTPUT_FILE}")
    if usuarios_nota:
        print(f"ℹ️ Nota sobre usuarios: {usuarios_nota}")

    await client.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
