import json, re
from collections import Counter

with open("msgs_data.json") as f:
    data = json.load(f)

# Buscar palabras clave
claves = ["hack", "vpn", ".onion"]
for palabra in claves:
    coincidencias = [m for m in data if palabra in m["texto"].lower()]
    print(palabra, "→", len(coincidencias), "mensajes")

# Extraer URLs
urls = re.findall(r'https?://\S+', " ".join(m["texto"] for m in data))
print("Total de URLs encontradas:", len(urls))

# Palabras más frecuentes
todas = " ".join(m["texto"] for m in data).split()
print(Counter(todas).most_common(5))
