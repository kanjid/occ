<h1 align="center">OCC · Laboratorio</h1>
<p align="center"><em>Operational Cyberintelligence Certificate</em> — material y entorno de prácticas de los módulos M2.12, M2.14 y M2.15.</p>

<p align="center">
  <a href="https://github.com/kanjid/occ"><img alt="GitHub" src="https://img.shields.io/badge/GitHub-kanjid%2Focc-181717?style=for-the-badge&logo=github&logoColor=white"></a>
  <img alt="Telegram OSINT" src="https://img.shields.io/badge/Telegram-OSINT-26A5E4?style=for-the-badge&logo=telegram&logoColor=white">
  <img alt="OSINT · CTI" src="https://img.shields.io/badge/OSINT-CTI-5E35B1?style=for-the-badge&logo=tor&logoColor=white">
  <img alt="Estado: en desarrollo" src="https://img.shields.io/badge/estado-en%20desarrollo-orange?style=for-the-badge">
</p>

---

Este repositorio monta, con **un solo comando**, todo el laboratorio del curso sobre una VM de **Kali Linux**: los scripts de las prácticas y la plataforma **Watcher** (CTI) ya levantada y funcionando. El alumno no tiene que instalar nada a mano.

## 1. Instalación

En la VM de Kali, abre una terminal y ejecuta:

```bash
curl -fsSL https://raw.githubusercontent.com/kanjid/occ/main/install.sh | bash
```

Eso es todo. El instalador se encarga del resto.

### Requisitos

- **Kali Linux** (o Debian) con conexión a internet.
- Usuario con permisos de **sudo**.
- Recomendado: **4 GB de RAM** y **~10 GB de disco** libres (Watcher levanta varios contenedores).
- La primera instalación tarda unos **10-15 minutos** (descarga de imágenes Docker).

### Qué hace el instalador

1. Comprueba el sistema y la conexión.
2. Instala **Docker** y **Docker Compose** si no están.
3. Clona este repositorio en `~/occ`.
4. Crea un **entorno Python** (`~/occ/.venv`) con las dependencias de las prácticas.
5. Clona **Watcher** (versión fijada) y lo deja **levantado**.
6. Crea un **usuario administrador** y **siembra los feeds RSS** (Práctica 3 lista).

### Acceso a Watcher

Al terminar, abre el navegador de la VM en:

```
http://localhost:9002
```

| | |
|---|---|
| **Usuario** | `alumno` |
| **Contraseña** | `OccWatcher2026!` |

> Cambia la contraseña tras el primer acceso. El panel escucha solo en `localhost` de la propia VM.

### Gestión y problemas frecuentes

```bash
cd ~/occ/m215_cti/watcher/deployment
make down     # parar Watcher
make up       # volver a arrancar
```

- Si `docker` te pide permisos, **cierra y abre sesión** una vez (activa el grupo `docker`).
- Para usar los scripts de Python: `source ~/occ/.venv/bin/activate`.
- Si algo falla a mitad, **vuelve a lanzar el instalador**: es idempotente y retoma donde haga falta.

## 2. Contenido de cada carpeta

```
occ/
├── install.sh            Instalador único (el del comando de arriba)
├── requirements.txt      Dependencias de Python de las prácticas
├── m212_leaks/           Módulo 2.12 — Leaks y exfiltración
├── m214_osint_tg/        Módulo 2.14 — OSINT con bots de Telegram
└── m215_cti/             Módulo 2.15 — Inteligencia de ciberamenazas (Watcher)
```

### `m212_leaks/` — Leaks y exfiltración de información

| Carpeta | Contenido |
|---|---|
| `CTF/m212_leaks.py` | Script del reto (CTF): consultas y retos de análisis de filtraciones que el alumno resuelve e interpreta. |
| `panel_lab/telegram_hunt_console.html` | Panel web autónomo (threat hunting) con datos simulados, para practicar en el navegador sin conexión. |

### `m214_osint_tg/` — OSINT con bots de Telegram

Las seis prácticas con **Telethon**, de lo más simple a lo más completo. Cada una en su carpeta:

| Práctica | Script | Qué hace |
|---|---|---|
| 1 | `practica_1/hello_tg.py` | Primer contacto: lista tus diálogos y valida las credenciales. |
| 2 | `practica_2/msg_group.py` | Exporta los mensajes de un grupo público a JSON enriquecido. |
| 3 | `practica_3/data.py` | Análisis OSINT básico: palabras clave, URLs y frecuencias. |
| 4 | `practica_4/collect.py` | Extrae enlaces, archivos y participantes. |
| 5 | `practica_5/automate.py` | Monitorización en tiempo real con alertas. |
| 6 | `practica_6/analisys.py` | Visualización y síntesis (pandas + matplotlib). |

> Recuerda: credenciales de Telegram **personales** (no se comparten), solo sobre **canales y grupos públicos**, y minimización de datos.

### `m215_cti/` — Inteligencia de ciberamenazas (Watcher)

Esta carpeta queda **vacía en el repositorio**: el instalador clona aquí **Watcher** (de `thalesgroup-cert`) en tiempo de instalación y lo levanta solo. Sobre él se hacen las cinco prácticas del módulo (dominios suplantados, fugas de datos, boletín de amenazas, ransomware/CVE y resumen de inteligencia).

---

<p align="center"><sub>Material docente de uso educativo. El laboratorio se realiza sobre datos públicos o de prueba, nunca contra sistemas de terceros sin autorización.</sub></p>
