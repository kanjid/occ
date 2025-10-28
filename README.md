# 🛰️ OCC Cyber Intelligence Course Repository

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)
![FastAPI](https://img.shields.io/badge/FastAPI-Enabled-009688?logo=fastapi)
![License](https://img.shields.io/badge/License-Academic-lightgrey)
![Status](https://img.shields.io/badge/Status-In%20Development-orange)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Docker%20%7C%20Armbian-lightblue)

---

## 🧭 Overview

This repository hosts the **training materials, scripts, and hands-on projects** for the **Cyber Intelligence specialization modules** at the **OCC (Cybercrime & Cyber Intelligence Observatory)**.  
Each module combines **applied Python**, **OSINT automation**, and **real-world threat analysis** to build practical tools for intelligence, monitoring, and investigation.

---

## 📦 Modules Included

| Module | Title | Description |
|:-------|:------|:-------------|
| **M2.12** | 🕵️‍♂️ *Leaks & Information Exfiltration* | Techniques and tools for detecting, analyzing, and mitigating data leaks and exfiltration incidents. |
| **M2.14** | 🤖 *OSINT Bot Creation for Telegram* | Learn to interact with Telegram’s API via **Telethon**, build OSINT bots, and automate data collection safely. |
| **M2.15** | 🧠 *Cyber Threat Intelligence (CTI)* | Correlation, enrichment, and visualization of threat intelligence from multiple sources. |

> 🧩 *All modules are designed for security analysts, researchers, and students with a basic Python background.*

---

## 🔍 M2.14 – OSINT Bot Creation for Telegram

This module focuses on **Telegram data collection and analysis** through the `Telethon` library and **Python 3.11**.  
You will learn how to:
- Connect to the Telegram API (MTProto protocol)
- Extract messages, media, links, and users from groups and channels
- Analyze and export structured data in JSON or CSV
- Automate keyword alerts and monitoring with asynchronous scripts
- Deploy your monitoring bot in **Docker** for secure and persistent execution

### 📁 Folder structure

```
M2.14
M2.12
M2.15
README.md
```

---

## 🧰 Technologies & Tools

| Tool | Purpose |
|------|----------|
| 🐍 **Python 3.11** | Core scripting and automation |
| 💬 **Telethon** | Telegram API interaction |
| 🐳 (optional) **Docker & Docker Compose** | Deployment and isolation |
| 📊 **JSON / CSV** | Structured OSINT data export |
| 🔐 **.env Configuration** | Secure handling of API credentials |
| 🧾 (optional) **IceCream Logger** | Real-time debugging and execution tracing |

---

## 🚀 Quick Start (M2.14 Example)

### 1️⃣ Clone the repository
```bash
git clone https://github.com/occ.git
cd M2.14
...
```

### 2️⃣ Set up environment variables
Create a `.env` file based on `.env.example` if you need:
```bash
API_ID=your_api_id
API_HASH=your_api_hash
SESSION_NAME="session_osint"
```

### 3️⃣ Execute examples
```bash
python3 tgexample_1.py
```

---

## 🧠 Educational Focus

This repository is part of a **practical cyber intelligence curriculum**, emphasizing:
- Ethical data collection  
- Automation for investigative purposes  
- Secure and transparent code practices  
- Adaptability to real-world incident analysis

> ⚖️ All examples are designed for **educational and research purposes only.**

---

## 🧩 Upcoming Additions

| Planned | Module | Focus |
|:--------|:--------|:------|
| ✅ | M2.14 | Upload and test all Telethon-based scripts |
| ✅ | M2.12 | Data leak analysis and exfiltration monitoring |
| 🔜 | M2.15 | Threat enrichment and intelligence automation (CTI) |

---

## 🧠 Práctica: Extracción y Correlación de Leaks con Python + OSINT

Esta práctica te guiará paso a paso para analizar un conjunto de mensajes simulados con posibles leaks (filtraciones de datos).
Aprenderás a extraer entidades, correlacionarlas con fuentes OSINT reales (Hunter.io y URLScan.io) y guardar los resultados para análisis posterior.

### ⚙️ 1. Estructura del proyecto

Copia estos archivos en una misma carpeta:

```sh
/leaks_practica
│
├── leak_sample.json        # Datos de ejemplo
├── extract_entities.py     # Extrae emails, dominios, teléfonos, menciones, URLs
├── correlate_osint.py      # Correlaciona resultados con Hunter.io y URLScan.io
├── save_csv.py             # Exporta los datos finales a formato CSV
├── .env.example            # Plantilla de variables de entorno
└── requirements.txt        # Librerías necesarias
```
### 📦 2. Instalación

Asegúrate de tener Python 3.10 o superior instalado.

Ejecuta los siguientes comandos en tu terminal (o CMD en Windows):

python -m venv venv
source venv/bin/activate       # En Linux/Mac
venv\Scripts\activate.ps1      # En Windows

```sh
pip install -r requirements.txt
```

💡 Si no tienes el archivo requirements.txt, instala manualmente:

```sh
pip install python-dotenv requests email-validator phonenumbers urlextract tldextract
```

### 🔐 3. Configurar el archivo .env

Copia el archivo de ejemplo (si no está crealo tú mismo con notepad - recuerda que al tener el . delante puede estar oculto):

```sh
cp .env.example .env
```

Abre .env y reemplaza los valores por tus claves personales:

```sh
HUNTER_API_KEY=TU_API_KEY_DE_HUNTER
URLSCAN_API_KEY=TU_API_KEY_DE_URLSCAN
```

Guarda el archivo y ciérralo.

📘 Si no tienes las API keys, el script funcionará igual pero marcará las consultas como “simuladas”.

### 🧩 4. Paso 1 — Extracción de entidades

Ejecuta el primer script para analizar el JSON:
```sh
python extract_entities.py --input leak_sample.json --output entities.json
```

Esto creará un nuevo archivo entities.json con los emails, teléfonos, dominios, URLs y menciones encontradas en los mensajes.

Ejemplo de salida:

[INFO] 500 registros procesados.
[INFO] Archivo generado: entities.json

### 🌐 5. Paso 2 — Correlación OSINT

Correlaciona los datos extraídos con Hunter.io y URLScan.io:
```sh
python correlate_osint.py --input entities.json --output correlated.json --limit 10
```

🔹 Este paso usa tus claves del .env.
🔹 Solo se procesarán 10 registros (para evitar límites de API).
🔹 Si tienes buena conexión o cuentas premium, puedes aumentar el límite:

python correlate_osint.py --limit 25


Generará correlated.json, que contendrá la validación de correos (Hunter) y escaneos de dominios (URLScan).

### 📊 6. Paso 3 — Guardar resultados en CSV

Convierte los resultados JSON a formato CSV (fácil de abrir en Excel):
```sh
python save_csv.py --input correlated.json --output resultados.csv
```

Esto creará un archivo resultados.csv con columnas como:

	Fecha (ts)

	Fuente (from)

	Correo (email)

	Dominio (domain)

	Estado (note)

	Resultado Hunter

	Resultado URLScan

### 📘 7. Archivos finales esperados

Tras ejecutar los tres scripts, deberías tener:
```sh
/leaks_practica
│
├── leak_sample.json
├── entities.json
├── correlated.json
├── resultados.csv
└── .env
```
### 🧠 8. Qué se aprende

✔️ A procesar leaks simulados sin usar expresiones regulares
✔️ A validar correos y dominios mediante APIs OSINT
✔️ A interpretar resultados de Hunter.io y URLScan.io
✔️ A exportar tus hallazgos para análisis en Excel o Power BI





---

## 🧑‍🏫 Author

**Ramón Fuentes**  
Cyber Intelligence Researcher & Educator  
🧠 OCC – Cybercrime & Cyber Intelligence Observatory  
📧 [rfuentes@cpcm.es](mailto:rfuentes@cpcm.es)

---

## 🧾 License

This repository and its contents are distributed for **academic and research purposes** only.  
Unauthorized commercial use or redistribution is not permitted.

---

## 🌐 References

- [Telethon Documentation](https://docs.telethon.dev)
- [Telegram MTProto Protocol](https://core.telegram.org/mtproto)
- [Docker Docs](https://docs.docker.com/)
- [Python Asyncio Guide](https://docs.python.org/3/library/asyncio.html)

---

> _“Intelligence is not about data collection — it’s about meaningful interpretation.”_  
> — OCC Training Program, 2025
