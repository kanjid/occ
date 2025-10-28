🧠 Práctica: Extracción y Correlación de Leaks con Python + OSINT

Esta práctica te guiará paso a paso para analizar un conjunto de mensajes simulados con posibles leaks (filtraciones de datos).
Aprenderás a extraer entidades, correlacionarlas con fuentes OSINT reales (Hunter.io y URLScan.io) y guardar los resultados para análisis posterior.

⚙️ 1. Estructura del proyecto

Copia estos archivos en una misma carpeta:

/leaks_practica
│
├── leak_sample.json        # Datos de ejemplo
├── extract_entities.py     # Extrae emails, dominios, teléfonos, menciones, URLs
├── correlate_osint.py      # Correlaciona resultados con Hunter.io y URLScan.io
├── save_csv.py             # Exporta los datos finales a formato CSV
├── .env.example            # Plantilla de variables de entorno
└── requirements.txt        # Librerías necesarias

📦 2. Instalación

Asegúrate de tener Python 3.10 o superior instalado.

Ejecuta los siguientes comandos en tu terminal (o CMD en Windows):

python -m venv venv
source venv/bin/activate       # En Linux/Mac
venv\Scripts\activate.ps1      # En Windows

pip install -r requirements.txt


💡 Si no tienes el archivo requirements.txt, instala manualmente:

pip install python-dotenv requests email-validator phonenumbers urlextract tldextract

🔐 3. Configurar el archivo .env

Copia el archivo de ejemplo (si no está crealo tú mismo con notepad - recuerda que al tener el . delante puede estar oculto):

cp .env.example .env


Abre .env y reemplaza los valores por tus claves personales:

HUNTER_API_KEY=TU_API_KEY_DE_HUNTER
URLSCAN_API_KEY=TU_API_KEY_DE_URLSCAN


Guarda el archivo y ciérralo.

📘 Si no tienes las API keys, el script funcionará igual pero marcará las consultas como “simuladas”.

🧩 4. Paso 1 — Extracción de entidades

Ejecuta el primer script para analizar el JSON:

python extract_entities.py --input leak_sample.json --output entities.json


Esto creará un nuevo archivo entities.json con los emails, teléfonos, dominios, URLs y menciones encontradas en los mensajes.

Ejemplo de salida:

[INFO] 500 registros procesados.
[INFO] Archivo generado: entities.json

🌐 5. Paso 2 — Correlación OSINT

Correlaciona los datos extraídos con Hunter.io y URLScan.io:

python correlate_osint.py --input entities.json --output correlated.json --limit 10


🔹 Este paso usa tus claves del .env.
🔹 Solo se procesarán 10 registros (para evitar límites de API).
🔹 Si tienes buena conexión o cuentas premium, puedes aumentar el límite:

python correlate_osint.py --limit 25


Generará correlated.json, que contendrá la validación de correos (Hunter) y escaneos de dominios (URLScan).

📊 6. Paso 3 — Guardar resultados en CSV

Convierte los resultados JSON a formato CSV (fácil de abrir en Excel):

python save_csv.py --input correlated.json --output resultados.csv


Esto creará un archivo resultados.csv con columnas como:

Fecha (ts)

Fuente (from)

Correo (email)

Dominio (domain)

Estado (note)

Resultado Hunter

Resultado URLScan

📘 7. Archivos finales esperados

Tras ejecutar los tres scripts, deberías tener:

/leaks_practica
│
├── leak_sample.json
├── entities.json
├── correlated.json
├── resultados.csv
└── .env

🧠 8. Qué se aprende

✔️ A procesar leaks simulados sin usar expresiones regulares
✔️ A validar correos y dominios mediante APIs OSINT
✔️ A interpretar resultados de Hunter.io y URLScan.io
✔️ A exportar tus hallazgos para análisis en Excel o Power BI

