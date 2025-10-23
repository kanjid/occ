from telethon import TelegramClient

# Sustituye con tus credenciales
api_id = <ESCRIBE AQUÍ TU API_ID>
api_hash = <"ESCRIBE AQUÍ TU API_HASH">

# Crea la sesión
client = TelegramClient("my_session", api_id, api_hash)

async def main():
    # Listar los chats disponibles
    async for dialog in client.iter_dialogs():
        print(dialog.name, "=>", dialog.id)

with client:
    client.loop.run_until_complete(main())