#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCC · Operational Cyberintelligence Certificate
M2.12 · Leaks: exfiltración de información
PRÁCTICA GUIADA: "¿Mis datos están en una filtración?"

Cómo se ejecuta (en la máquina virtual Kali):
    python3 m212_leaks.py

No necesita instalar nada ni crear cuentas: solo usa Python y servicios públicos.

CONSULTAS BÁSICAS
  1. Correo     -> XposedOrNot (filtraciones conocidas)
  2. Contraseña -> Have I Been Pwned · Pwned Passwords (k-anonimato)
  3. Dominio    -> crt.sh (registros públicos de certificados)
  4. Modo demostración (sin Internet, datos ficticios)

RETOS DE ANÁLISIS (el script trae los datos; el alumno los interpreta)
  5. Anatomía de una brecha          -> catálogo público de Have I Been Pwned
  6. Tendencias de las filtraciones  -> catálogo completo de Have I Been Pwned
  7. Huella pública de un dominio    -> crt.sh + DNS (SPF y DMARC)
  8. Patrones de contraseñas         -> Pwned Passwords
  9. Caso integrador                 -> retos 5 y 7 sobre una misma organización

Cada consulta y cada respuesta del alumno se guardan en un informe .txt en esta carpeta.

PARA EL DOCENTE (antes de clase, con Internet):
    python3 m212_leaks.py --preparar dominio-de-la-clase.es
Descarga el catálogo de brechas y los certificados del dominio en la carpeta
"cache". Copia esa carpeta junto al script de cada alumno y los retos 5 a 9
funcionarán aunque los servicios estén saturados o falle la red.

USO EXCLUSIVAMENTE DOCENTE. Consulta solo datos propios o de prueba.
"""

import getpass
import hashlib
import json
import os
import re
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime

VERSION = "2.0 (noviembre 2026)"
AGENTE = "OCC-M2.12-Practica-Docente/2.0"
CARPETA = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(CARPETA, "cache")
ALUMNO = ""
INFORME = os.path.join(CARPETA, "informe_M2-12_" + datetime.now().strftime("%Y%m%d_%H%M") + ".txt")

# ---------------------------------------------------------------- colores
if sys.stdout.isatty() and os.name != "nt":
    AZUL, VERDE, AMARILLO, ROJO, GRIS, NEGRITA, FIN = (
        "\033[94m", "\033[92m", "\033[93m", "\033[91m", "\033[90m", "\033[1m", "\033[0m")
else:
    AZUL = VERDE = AMARILLO = ROJO = GRIS = NEGRITA = FIN = ""


def titulo(texto):
    print("\n" + AZUL + NEGRITA + "═" * 64 + "\n  " + texto + "\n" + "═" * 64 + FIN)


def observacion(texto):
    print(AZUL + "  [OBSERVACIÓN]  " + FIN + texto)


def inferencia(texto):
    print(AMARILLO + "  [INFERENCIA]   " + FIN + texto)


def pendiente(texto):
    print(GRIS + "  [VERIFICAR]    " + FIN + texto)


def aviso(texto):
    print(ROJO + "  ⚠ " + texto + FIN)


# ---------------------------------------------------------------- informe
def registrar(tipo, consulta, fuente, observaciones, inferencias, verificar):
    """Guarda el hallazgo en el informe: qué, cuándo, con qué fuente y qué conclusión."""
    lineas = [
        "-" * 64,
        "Fecha y hora : " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "Tipo         : " + tipo,
        "Consulta     : " + consulta,
        "Fuente       : " + fuente,
        "OBSERVACIÓN  :",
    ] + ["   - " + o for o in observaciones] + ["INFERENCIA   :"] + \
        ["   - " + i for i in inferencias] + ["VERIFICAR    :"] + \
        ["   - " + v for v in verificar] + [""]
    escribir_informe(lineas)
    print(VERDE + "\n  ✔ Hallazgo guardado en: " + FIN + os.path.basename(INFORME))


def escribir_informe(lineas):
    nuevo = not os.path.exists(INFORME)
    with open(INFORME, "a", encoding="utf-8") as f:
        if nuevo:
            f.write("INFORME DE PRÁCTICA · OCC M2.12 · Leaks\n")
            f.write("Generado por m212_leaks.py v" + VERSION + "\n")
            f.write("Alumno/a    : " + (ALUMNO or "(sin indicar)") + "\n\n")
        f.write("\n".join(lineas) + "\n")


def preguntar(reto, preguntas):
    """Plantea las preguntas de interpretación y guarda las respuestas en el informe."""
    print("\n" + AMARILLO + NEGRITA + "  ✎ AHORA TE TOCA A TI: interpreta los datos de arriba" + FIN)
    print(GRIS + "  Responde con tus palabras (una o dos frases) y pulsa Intro." + FIN)
    print(GRIS + "  Si no sabes qué responder, pulsa Intro y lo comentamos en clase." + FIN)
    lineas = ["=" * 64, "RESPUESTAS · " + reto, "Fecha y hora : " + datetime.now().strftime("%d/%m/%Y %H:%M:%S")]
    for n, p in enumerate(preguntas, 1):
        print("\n  " + NEGRITA + "P" + str(n) + ". " + FIN + p)
        try:
            r = input("  → ").strip()
        except EOFError:
            r = ""
        lineas += ["P" + str(n) + ". " + p, "   R: " + (r or "(sin responder)")]
    lineas.append("")
    escribir_informe(lineas)
    print(VERDE + "\n  ✔ Respuestas guardadas en: " + FIN + os.path.basename(INFORME))


# ---------------------------------------------------------------- red
def descargar(url, cabeceras=None, espera=30):
    """Devuelve (codigo_http, texto). codigo 0 = sin conexión."""
    peticion = urllib.request.Request(url, headers={"User-Agent": AGENTE, **(cabeceras or {})})
    try:
        with urllib.request.urlopen(peticion, timeout=espera) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            cuerpo = e.read().decode("utf-8", errors="replace")
        except Exception:
            cuerpo = ""
        return e.code, cuerpo
    except Exception:
        return 0, ""


def explicar_error(codigo, servicio):
    if codigo == 0:
        aviso("No hay conexión con " + servicio + ". Comprueba Internet o usa la opción 4 (demostración).")
    elif codigo == 429:
        aviso(servicio + " ha alcanzado su límite de consultas (toda el aula comparte conexión).")
        aviso("Espera unos minutos o usa la opción 4 (demostración).")
    elif codigo >= 500:
        aviso(servicio + " está saturado ahora mismo (error " + str(codigo) + "). Prueba más tarde o usa la opción 4.")
    else:
        aviso(servicio + " respondió con un error inesperado (" + str(codigo) + ").")


# ================================================================ 1. CORREO
def consultar_correo(demo=False):
    titulo("1 · ¿Aparece este correo en filtraciones conocidas?")
    print("  Usa SOLO tu propio correo o uno de prueba. Consultar correos ajenos")
    print("  es tratar datos personales de otra persona (RGPD).\n")
    if demo:
        correo = "alumno.demo@ejemplo.es"
        print("  Correo de demostración: " + correo)
        datos = DEMO_CORREO
    else:
        correo = input("  Escribe el correo y pulsa Intro: ").strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
            aviso("Eso no parece un correo válido (ejemplo: nombre@dominio.es).")
            return
        print(GRIS + "  Consultando XposedOrNot…" + FIN)
        codigo, texto = descargar("https://api.xposedornot.com/v1/breach-analytics?email="
                                  + urllib.parse.quote(correo))
        if codigo != 200:
            explicar_error(codigo, "XposedOrNot")
            return
        try:
            datos = json.loads(texto)
        except ValueError:
            aviso("La respuesta no se ha podido leer. Usa la opción 4.")
            return

    detalles = ((datos.get("ExposedBreaches") or {}).get("breaches_details")) or []
    print()
    if not detalles:
        observacion("El correo NO aparece en las filtraciones que conoce XposedOrNot.")
        inferencia("No hay indicios de exposición en esta fuente.")
        pendiente("'No aparece' no significa 'nunca filtrado': cada fuente conoce solo una parte.")
        registrar("Correo", correo, "XposedOrNot" + (" (DEMO)" if demo else ""),
                  ["Sin resultados en XposedOrNot."],
                  ["Sin indicios de exposición en esta fuente."],
                  ["Contrastar con otra fuente (p. ej. web de Have I Been Pwned)."])
        return

    observacion("El correo aparece en " + NEGRITA + str(len(detalles)) + FIN + " filtración(es):\n")
    print("     {:<22} {:<6} {:<38}".format("Filtración", "Año", "Datos expuestos"))
    print("     " + "-" * 66)
    obs, contrasenas = [], False
    for b in detalles:
        nombre = str(b.get("breach", "?"))[:22]
        anio = str(b.get("xposed_date", "?"))
        crudos = [d.strip() for d in str(b.get("xposed_data", "")).split(";") if d.strip()]
        expuestos = ", ".join(TRADUCCION.get(d, d) for d in crudos)
        if any("password" in d.lower() for d in crudos):
            contrasenas = True
        print("     {:<22} {:<6} {}".format(nombre, anio, expuestos[:60]))
        obs.append("{} ({}): {}".format(nombre, anio, expuestos))
    print()
    infs = ["El correo estuvo expuesto en al menos " + str(len(detalles)) + " incidente(s)."]
    inferencia(infs[0])
    if contrasenas:
        infs.append("Alguna filtración incluía contraseñas: si se reutilizan, la cuenta está en riesgo.")
        inferencia(infs[1])
    ver = ["Confirmar cada filtración en una segunda fuente (Have I Been Pwned).",
           "Que el correo aparezca no prueba que la contraseña actual sea la filtrada."]
    for v in ver:
        pendiente(v)
    registrar("Correo", correo, "XposedOrNot · breach-analytics" + (" (DEMO)" if demo else ""), obs, infs, ver)


# ============================================================ 2. CONTRASEÑA
def consultar_contrasena(demo=False):
    titulo("2 · ¿Esta contraseña aparece en filtraciones? (sin enviarla)")
    print("  NO escribas tu contraseña real. Prueba con ejemplos como: 123456, Verano2024, Madrid1\n")
    if demo:
        clave = "Verano2024"
        print("  Contraseña de demostración: " + clave)
    else:
        clave = getpass.getpass("  Escribe la contraseña de prueba (no se verá al teclear) y pulsa Intro: ")
        if not clave:
            aviso("No has escrito nada.")
            return

    resumen = hashlib.sha1(clave.encode("utf-8")).hexdigest().upper()
    prefijo, sufijo = resumen[:5], resumen[5:]
    print("\n  " + NEGRITA + "Así protege tu privacidad el k-anonimato:" + FIN)
    print("   1) Tu ordenador convierte la contraseña en una huella (hash SHA-1):")
    print("        " + AZUL + prefijo + FIN + sufijo)
    print("   2) Solo se envían a Internet los 5 primeros caracteres: " + AZUL + NEGRITA + prefijo + FIN)
    print("   3) El servicio devuelve cientos de huellas que empiezan igual,")
    print("      y TU ordenador busca la tuya entre ellas.\n")

    if demo:
        veces = DEMO_CONTRASENA_VECES  # cifra ficticia
        candidatas = DEMO_CONTRASENA_CANDIDATAS
    else:
        print(GRIS + "  Consultando Pwned Passwords…" + FIN)
        codigo, texto = descargar("https://api.pwnedpasswords.com/range/" + prefijo,
                                  {"Add-Padding": "true"})
        if codigo != 200:
            explicar_error(codigo, "Pwned Passwords")
            return
        veces, candidatas = 0, 0
        for linea in texto.splitlines():
            if ":" not in linea:
                continue
            suf, num = linea.strip().split(":", 1)
            if int(num) > 0:
                candidatas += 1
            if suf.upper() == sufijo:
                veces = int(num)

    observacion("Se recibieron " + str(candidatas) + " huellas candidatas con el prefijo " + prefijo + ".")
    if veces:
        observacion("Tu huella aparece " + NEGRITA + "{:,}".format(veces).replace(",", ".") + FIN
                    + " veces en filtraciones.")
        infs = ["Contraseña comprometida: no debe usarse en ninguna cuenta."]
    else:
        observacion("Tu huella NO aparece en la base de datos.")
        infs = ["No consta en filtraciones conocidas (no significa que sea segura)."]
    inferencia(infs[0])
    ver = ["La contraseña real nunca salió del equipo: solo el prefijo " + prefijo + "."]
    pendiente(ver[0])
    registrar("Contraseña (k-anonimato)", "prefijo SHA-1 " + prefijo + " (la contraseña NO se guarda)",
              "Have I Been Pwned · Pwned Passwords" + (" (DEMO)" if demo else ""),
              [str(candidatas) + " huellas candidatas recibidas.",
               ("Coincidencia: " + str(veces) + " apariciones.") if veces else "Sin coincidencia."],
              infs, ver)


# =============================================================== 3. DOMINIO
def limpiar_dominio(texto):
    texto = texto.strip().lower()
    texto = re.sub(r"^[a-z]+://", "", texto).split("/")[0].split(":")[0]
    return texto[4:] if texto.startswith("www.") else texto


def consultar_dominio(demo=False):
    titulo("3 · ¿Qué subdominios ha publicado una organización?")
    print("  Los certificados de seguridad (el candado HTTPS) se registran en listas públicas.")
    print("  Revisarlas muestra qué servicios ha puesto en marcha un dominio y cuándo.\n")
    if demo:
        dominio = "ejemplo-curso.es"
        print("  Dominio de demostración: " + dominio)
        registros = DEMO_DOMINIO
    else:
        dominio = limpiar_dominio(input("  Escribe un dominio (ej.: universidad.es) y pulsa Intro: "))
        if "." not in dominio or " " in dominio:
            aviso("Eso no parece un dominio (ejemplo: midominio.es).")
            return
        print(GRIS + "  Consultando crt.sh (puede tardar hasta 1 minuto)…" + FIN)
        codigo, texto = 0, ""
        for _ in range(2):  # crt.sh se satura a menudo: un reintento
            codigo, texto = descargar("https://crt.sh/?q=" + urllib.parse.quote("%." + dominio)
                                      + "&output=json", espera=60)
            if codigo == 200:
                break
        if codigo != 200:
            explicar_error(codigo, "crt.sh")
            return
        try:
            registros = json.loads(texto) if texto.strip() else []
        except ValueError:
            aviso("crt.sh devolvió una respuesta incompleta. Prueba de nuevo o usa la opción 4.")
            return

    subdominios = {}
    for r in registros:
        fecha = str(r.get("not_before", ""))[:10]
        for nombre in str(r.get("name_value", "")).split("\n"):
            nombre = nombre.strip().lower().lstrip("*.")
            if nombre.endswith(dominio):
                if nombre not in subdominios or fecha < subdominios[nombre]:
                    subdominios[nombre] = fecha
    print()
    if not subdominios:
        observacion("No se han encontrado certificados para " + dominio + ".")
        pendiente("Revisa que el dominio esté bien escrito.")
        registrar("Dominio", dominio, "crt.sh" + (" (DEMO)" if demo else ""),
                  ["Sin certificados registrados."], ["Sin datos para inferir."],
                  ["Comprobar la escritura del dominio."])
        return

    lista = sorted(subdominios.items(), key=lambda x: x[1])
    observacion(str(len(registros)) + " certificados → " + NEGRITA + str(len(lista)) + FIN
                + " nombres distintos. Los 15 más antiguos:\n")
    print("     {:<12} {}".format("Primer cert.", "Subdominio"))
    print("     " + "-" * 50)
    for nombre, fecha in lista[:15]:
        print("     {:<12} {}".format(fecha, nombre))
    if len(lista) > 15:
        print(GRIS + "     … y " + str(len(lista) - 15) + " más (todos guardados en el informe)." + FIN)
    print()
    sensibles = [n for n, _ in lista if re.search(r"(vpn|mail|correo|admin|dev|test|intranet|portal|login)", n)]
    infs = ["La organización publica al menos " + str(len(lista)) + " servicios con HTTPS."]
    inferencia(infs[0])
    if sensibles:
        infs.append("Nombres que sugieren servicios internos o de acceso: " + ", ".join(sensibles[:5]))
        inferencia(infs[1])
    ver = ["Tener certificado no prueba que el servicio siga activo hoy.",
           "No acceder a esos servicios: la práctica es solo observar registros públicos."]
    for v in ver:
        pendiente(v)
    registrar("Dominio", dominio, "crt.sh · Certificate Transparency" + (" (DEMO)" if demo else ""),
              [f + "  " + n for n, f in lista], infs, ver)


TRADUCCION = {
    "Email addresses": "correos", "Passwords": "contraseñas", "Usernames": "usuarios",
    "Names": "nombres", "Phone numbers": "teléfonos", "Password hints": "pistas de contraseña",
    "Geographic locations": "ubicaciones", "IP addresses": "direcciones IP",
    "Dates of birth": "fechas de nacimiento", "Physical addresses": "direcciones postales",
    "Genders": "género", "Job titles": "cargos", "Employers": "empresas",
    "Social media profiles": "perfiles en redes", "Credit cards": "tarjetas",
}

# ===================================================== datos de demostración
# FICTICIOS: el correo y el dominio no existen. Los nombres de filtraciones
# son incidentes públicos reales, pero su asociación a este correo es inventada.
DEMO_CORREO = {"ExposedBreaches": {"breaches_details": [
    {"breach": "LinkedIn", "xposed_date": "2012",
     "xposed_data": "Email addresses;Passwords"},
    {"breach": "Adobe", "xposed_date": "2013",
     "xposed_data": "Email addresses;Password hints;Passwords;Usernames"},
    {"breach": "Canva", "xposed_date": "2019",
     "xposed_data": "Email addresses;Geographic locations;Names;Passwords;Usernames"},
]}}
DEMO_CONTRASENA_VECES = 4213
DEMO_CONTRASENA_CANDIDATAS = 812
DEMO_DOMINIO = [
    {"not_before": "2019-03-02T00:00:00", "name_value": "ejemplo-curso.es\nwww.ejemplo-curso.es"},
    {"not_before": "2020-06-15T00:00:00", "name_value": "correo.ejemplo-curso.es"},
    {"not_before": "2021-01-10T00:00:00", "name_value": "vpn.ejemplo-curso.es"},
    {"not_before": "2022-09-21T00:00:00", "name_value": "campus.ejemplo-curso.es"},
    {"not_before": "2023-11-05T00:00:00", "name_value": "test-campus.ejemplo-curso.es"},
    {"not_before": "2024-04-18T00:00:00", "name_value": "*.ejemplo-curso.es"},
]
# Catálogo de demostración: incidentes públicos reales, cifras redondeadas a modo de ejemplo.
DEMO_CATALOGO = [
    {"Name": "LinkedIn", "Title": "LinkedIn", "Domain": "linkedin.com", "BreachDate": "2012-05-05",
     "AddedDate": "2016-05-21T21:35:40Z", "PwnCount": 164611595, "IsVerified": True,
     "IsStealerLog": False, "DataClasses": ["Email addresses", "Passwords"]},
    {"Name": "Adobe", "Title": "Adobe", "Domain": "adobe.com", "BreachDate": "2013-10-04",
     "AddedDate": "2013-12-04T00:00:00Z", "PwnCount": 152445165, "IsVerified": True,
     "IsStealerLog": False, "DataClasses": ["Email addresses", "Password hints", "Passwords", "Usernames"]},
    {"Name": "Canva", "Title": "Canva", "Domain": "canva.com", "BreachDate": "2019-05-24",
     "AddedDate": "2019-08-08T00:00:00Z", "PwnCount": 137272116, "IsVerified": True,
     "IsStealerLog": False, "DataClasses": ["Email addresses", "Geographic locations", "Names",
                                            "Passwords", "Usernames"]},
    {"Name": "Dropbox", "Title": "Dropbox", "Domain": "dropbox.com", "BreachDate": "2012-07-01",
     "AddedDate": "2016-08-30T23:49:49Z", "PwnCount": 68648009, "IsVerified": True,
     "IsStealerLog": False, "DataClasses": ["Email addresses", "Passwords"]},
    {"Name": "MySpace", "Title": "MySpace", "Domain": "myspace.com", "BreachDate": "2008-07-01",
     "AddedDate": "2016-05-31T00:00:00Z", "PwnCount": 359420698, "IsVerified": True,
     "IsStealerLog": False, "DataClasses": ["Email addresses", "Passwords", "Usernames"]},
    {"Name": "Yahoo", "Title": "Yahoo", "Domain": "yahoo.com", "BreachDate": "2014-09-01",
     "AddedDate": "2016-12-15T00:00:00Z", "PwnCount": 500000000, "IsVerified": True,
     "IsStealerLog": False, "DataClasses": ["Dates of birth", "Email addresses", "Names",
                                            "Passwords", "Phone numbers"]},
]
DEMO_TXT = {"ejemplo-curso.es": ["v=spf1 include:_spf.google.com ~all"],
            "_dmarc.ejemplo-curso.es": ["v=DMARC1; p=none; rua=mailto:dmarc@ejemplo-curso.es"]}
DEMO_PATRONES = {"123456": 41900000, "password": 10400000, "Verano2024": 112, "Madrid2024!": 38,
                 "qwerty": 10900000, "P@ssw0rd": 180000, "Barcelona1": 14500, "Tr0ub4dor&3": 9,
                 "frase": 0}


# ----------------------------------------------- utilidades de los retos
def ruta_cache(nombre):
    return os.path.join(CACHE, re.sub(r"[^a-z0-9._-]", "_", nombre.lower()) + ".json")


def leer_cache(nombre, max_dias=45):
    ruta = ruta_cache(nombre)
    if not os.path.exists(ruta):
        return None, None
    if (time.time() - os.path.getmtime(ruta)) / 86400 > max_dias:
        return None, None
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f), datetime.fromtimestamp(os.path.getmtime(ruta)).strftime("%d/%m/%Y")
    except (OSError, ValueError):
        return None, None


def guardar_cache(nombre, datos):
    try:
        os.makedirs(CACHE, exist_ok=True)
        with open(ruta_cache(nombre), "w", encoding="utf-8") as f:
            json.dump(datos, f)
    except OSError:
        pass


def barra(valor, maximo, ancho=26):
    return "█" * max(1, round(valor / maximo * ancho)) if valor and maximo > 0 else ""


def miles(n):
    return "{:,}".format(int(n)).replace(",", ".")


def fecha(texto):
    try:
        return datetime.strptime(str(texto)[:10], "%Y-%m-%d")
    except ValueError:
        return None


def traducir(clases):
    return [TRADUCCION.get(c, c) for c in clases]


def ofrecer_demo(servicio):
    aviso("No se ha podido usar " + servicio + " (sin conexión o servicio saturado).")
    try:
        return input("  ¿Hacer el reto con datos de demostración? (s/n): ").strip().lower().startswith("s")
    except EOFError:
        return False


# ------------------------------------------------- catálogo de brechas (HIBP)
def catalogo_brechas(demo=False):
    """Catálogo público de Have I Been Pwned (sin clave). Devuelve (lista, origen)."""
    if demo:
        return DEMO_CATALOGO, "DEMOSTRACIÓN (datos ficticios)"
    datos, dia = leer_cache("hibp_breaches")
    if datos:
        return datos, "Have I Been Pwned · copia local del " + dia
    print(GRIS + "  Descargando el catálogo de Have I Been Pwned…" + FIN)
    codigo, texto = descargar("https://haveibeenpwned.com/api/v3/breaches", espera=60)
    if codigo != 200:
        explicar_error(codigo, "Have I Been Pwned")
        return None, None
    try:
        datos = json.loads(texto)
    except ValueError:
        aviso("La respuesta de Have I Been Pwned no se ha podido leer.")
        return None, None
    guardar_cache("hibp_breaches", datos)
    return datos, "Have I Been Pwned · descargado el " + datetime.now().strftime("%d/%m/%Y")


def reto_anatomia(demo=False):
    titulo("5 · Anatomía de una brecha: ¿qué se filtró y cuánto tardó en saberse?")
    print("  El script trae la ficha pública de una brecha famosa. Tú la interpretas.\n")
    catalogo, origen = catalogo_brechas(demo)
    if not catalogo:
        if ofrecer_demo("Have I Been Pwned"):
            return reto_anatomia(demo=True)
        return
    porNombre = {b.get("Name"): b for b in catalogo}
    disponibles = [n for n in ("LinkedIn", "Adobe", "Canva", "Dropbox", "MySpace", "Yahoo") if n in porNombre]
    if not disponibles:
        disponibles = [b.get("Name") for b in catalogo[:6]]
    print("  Brechas disponibles para analizar:")
    for i, n in enumerate(disponibles[:6], 1):
        print("   " + str(i) + ") " + str(porNombre.get(n, {}).get("Title", n)))
    try:
        sel = input("\n  Elige un número (o Intro para la primera): ").strip()
    except EOFError:
        sel = ""
    idx = int(sel) - 1 if sel.isdigit() and 1 <= int(sel) <= len(disponibles[:6]) else 0
    b = porNombre[disponibles[idx]]

    inicio, alta = fecha(b.get("BreachDate")), fecha(b.get("AddedDate"))
    retraso = (alta - inicio).days if inicio and alta else None
    clases = traducir(b.get("DataClasses") or [])
    sino = lambda v: "sí" if v else "no"
    print()
    observacion("Ficha de " + str(b.get("Title", "?")) + ":\n")
    filas = [
        ("Dominio", str(b.get("Domain") or "(no consta)")),
        ("Fecha de la brecha", str(b.get("BreachDate", "?"))),
        ("Añadida al catálogo", str(b.get("AddedDate", "?"))[:10]),
        ("Cuentas afectadas", miles(b.get("PwnCount", 0))),
        ("Verificada", sino(b.get("IsVerified"))),
        ("Es un stealer log", sino(b.get("IsStealerLog"))),
        ("Datos expuestos", ", ".join(clases)),
    ]
    for k, v in filas:
        print("     {:<22}{}".format(k + ":", v))
    if retraso is not None:
        print("\n     " + NEGRITA + "Entre la brecha y su publicación pasaron " + str(retraso)
              + " días." + FIN)
    print(GRIS + "\n  Fuente: " + origen + FIN)

    preguntar("Reto 5 · Anatomía de una brecha (" + str(b.get("Title", "?")) + ")", [
        "¿Cuántos días pasaron entre la brecha y su publicación? ¿Qué problema supone esa ventana de tiempo?",
        "De los datos expuestos, ¿cuál es el más peligroso para la víctima y por qué?",
        "El campo 'Verificada' indica si HIBP confirmó la brecha. ¿Por qué es una OBSERVACIÓN y no una INFERENCIA?",
    ])


def reto_tendencias(demo=False):
    titulo("6 · Tendencias: ¿qué datos se filtran más y en qué años?")
    print("  El script resume TODO el catálogo de brechas conocidas. Tú lees los patrones.\n")
    catalogo, origen = catalogo_brechas(demo)
    if not catalogo:
        if ofrecer_demo("Have I Been Pwned"):
            return reto_tendencias(demo=True)
        return

    total = len(catalogo)
    porAnio = Counter()
    porClase = Counter()
    stealer = 0
    for b in catalogo:
        d = fecha(b.get("BreachDate"))
        if d:
            porAnio[d.year] += 1
        for c in traducir(b.get("DataClasses") or []):
            porClase[c] += 1
        if b.get("IsStealerLog"):
            stealer += 1

    observacion("El catálogo tiene " + NEGRITA + miles(total) + FIN + " brechas registradas.\n")
    print("  " + NEGRITA + "Datos más filtrados (nº de brechas que los incluían):" + FIN)
    tope = porClase.most_common(1)[0][1] if porClase else 1
    for nombre, n in porClase.most_common(8):
        print("     {:<24}{:>6}  {}".format(nombre[:23], miles(n), barra(n, tope)))

    anios = sorted(a for a in porAnio if a >= 2007)
    if anios:
        print("\n  " + NEGRITA + "Brechas por año de la brecha:" + FIN)
        topeA = max(porAnio[a] for a in anios)
        for a in anios:
            print("     {:<6}{:>5}  {}".format(a, porAnio[a], barra(porAnio[a], topeA)))
    print("\n     Brechas marcadas como 'stealer log': " + miles(stealer)
          + " de " + miles(total) + ".")
    print(GRIS + "\n  Fuente: " + origen + FIN)

    preguntar("Reto 6 · Tendencias del catálogo", [
        "¿Qué tipo de dato aparece en más filtraciones? ¿Por qué crees que es el más frecuente?",
        "Mira los años: ¿el número de brechas registradas sube, baja o es irregular? Da una posible explicación.",
        "Que un año reciente tenga MENOS brechas registradas no significa que hubiera menos. ¿Qué otra explicación hay? (pista: el retraso del reto 5).",
    ])


# --------------------------------------------- huella de dominio (crt.sh + DNS)
def certificados_dominio(dominio, demo=False):
    if demo:
        return DEMO_DOMINIO, "DEMOSTRACIÓN (datos ficticios)"
    datos, dia = leer_cache("crtsh_" + dominio)
    if datos:
        return datos, "crt.sh · copia local del " + dia
    print(GRIS + "  Consultando crt.sh (puede tardar hasta un minuto)…" + FIN)
    codigo, texto = 0, ""
    for _ in range(2):
        codigo, texto = descargar("https://crt.sh/?q=" + urllib.parse.quote("%." + dominio)
                                  + "&output=json", espera=60)
        if codigo == 200:
            break
    if codigo != 200:
        explicar_error(codigo, "crt.sh")
        return None, None
    try:
        datos = json.loads(texto) if texto.strip() else []
    except ValueError:
        aviso("crt.sh devolvió una respuesta incompleta.")
        return None, None
    guardar_cache("crtsh_" + dominio, datos)
    return datos, "crt.sh · descargado el " + datetime.now().strftime("%d/%m/%Y")


def consulta_dns_txt(dominio, demo=False):
    """Devuelve la lista de registros TXT de un dominio vía DNS over HTTPS (Cloudflare)."""
    if demo:
        return DEMO_TXT.get(dominio, [])
    url = "https://cloudflare-dns.com/dns-query?name=" + urllib.parse.quote(dominio) + "&type=TXT"
    codigo, texto = descargar(url, {"Accept": "application/dns-json"})
    if codigo != 200:
        return None
    try:
        datos = json.loads(texto)
    except ValueError:
        return None
    return [r.get("data", "").strip('"') for r in (datos.get("Answer") or [])]


def reto_huella(demo=False):
    titulo("7 · Huella pública de un dominio: ¿qué deja ver sin entrar en él?")
    print("  Combinamos dos fuentes abiertas: los certificados (crt.sh) y el DNS.")
    print("  Son datos que cualquiera puede ver; no se accede a ningún sistema.\n")
    if demo:
        dominio = "ejemplo-curso.es"
        print("  Dominio de demostración: " + dominio)
    else:
        try:
            dominio = limpiar_dominio(input("  Escribe un dominio (ej.: universidad.es): "))
        except EOFError:
            dominio = ""
        if "." not in dominio or " " in dominio:
            aviso("Eso no parece un dominio.")
            return

    registros, origen = certificados_dominio(dominio, demo)
    if registros is None:
        if ofrecer_demo("crt.sh"):
            return reto_huella(demo=True)
        return

    subs = {}
    for r in registros:
        f = str(r.get("not_before", ""))[:10]
        for nombre in str(r.get("name_value", "")).split("\n"):
            nombre = nombre.strip().lower().lstrip("*.")
            if nombre.endswith(dominio) and (nombre not in subs or f < subs[nombre]):
                subs[nombre] = f
    lista = sorted(subs.items(), key=lambda x: x[1] or "9999")
    print()
    observacion(miles(len(registros)) + " certificados → " + NEGRITA + str(len(lista)) + FIN
                + " nombres distintos. Los 12 más antiguos:\n")
    print("     {:<12}{}".format("1er cert.", "Subdominio"))
    for nombre, f in lista[:12]:
        print("     {:<12}{}".format(f or "?", nombre))

    pistas = {"vpn": "acceso remoto", "mail": "correo", "correo": "correo", "webmail": "correo",
              "admin": "administración", "dev": "desarrollo", "test": "pruebas", "pre": "preproducción",
              "intranet": "red interna", "portal": "portal", "login": "acceso", "sso": "acceso único",
              "git": "repositorio de código", "jenkins": "integración continua"}
    marcados = [(n, pistas[p]) for n, _ in lista for p in pistas if p in n.split(".")[0]]
    if marcados:
        print("\n  " + NEGRITA + "Nombres que sugieren servicios internos o sensibles:" + FIN)
        for n, etiqueta in marcados[:8]:
            print("     " + n + "  → posible " + etiqueta)

    print("\n  " + NEGRITA + "Correo del dominio (registros DNS TXT):" + FIN)
    txt = consulta_dns_txt(dominio, demo)
    if txt is None:
        pendiente("No se ha podido consultar el DNS ahora mismo.")
    else:
        spf = next((t for t in txt if t.lower().startswith("v=spf1")), None)
        print("     SPF (quién puede enviar correo en su nombre): "
              + (spf[:70] if spf else "no encontrado"))
        dmarc = consulta_dns_txt("_dmarc." + dominio, demo)
        dm = next((t for t in (dmarc or []) if t.lower().startswith("v=dmarc1")), None)
        print("     DMARC (política antifraude de correo): " + (dm[:70] if dm else "no encontrado"))
    print(GRIS + "\n  Fuente: " + origen + " · DNS vía Cloudflare DoH" + FIN)

    preguntar("Reto 7 · Huella pública de " + dominio, [
        "¿Qué servicios de la organización puedes NOMBRAR solo mirando los subdominios? ¿Cuál te parece más sensible?",
        "Ver un subdominio 'vpn' o 'admin' es una OBSERVACIÓN. Escribe una INFERENCIA a partir de él y qué habría que VERIFICAR antes de darla por cierta.",
        "Si el dominio no tiene DMARC o su política es 'p=none', ¿qué tipo de ataque facilita? (pista: suplantación de correo).",
    ])


def veces_filtrada(clave):
    """Nº de apariciones de una contraseña en Pwned Passwords (k-anonimato). -1 si falla."""
    resumen = hashlib.sha1(clave.encode("utf-8")).hexdigest().upper()
    codigo, texto = descargar("https://api.pwnedpasswords.com/range/" + resumen[:5],
                              {"Add-Padding": "true"})
    if codigo != 200:
        return -1
    for linea in texto.splitlines():
        if ":" in linea:
            suf, num = linea.strip().split(":", 1)
            if suf.upper() == resumen[5:]:
                return int(num)
    return 0


def reto_patrones(demo=False):
    titulo("8 · Patrones de contraseñas: ¿por qué unas caen y otras no?")
    print("  El script comprueba varias contraseñas de ejemplo (nunca las tuyas) y")
    print("  cuenta cuántas veces aparece cada una en filtraciones. Tú sacas la regla.\n")
    ejemplos = ["123456", "password", "Verano2024", "Madrid2024!", "qwerty",
                "P@ssw0rd", "Barcelona1", "Tr0ub4dor&3"]
    print("     {:<18}{:>18}".format("Contraseña", "Veces filtrada"))
    print("     " + "-" * 38)
    resultados = []
    for clave in ejemplos:
        if demo:
            veces = DEMO_PATRONES.get(clave, 0)
        else:
            veces = veces_filtrada(clave)
            time.sleep(0.3)
        if veces == -1:
            if ofrecer_demo("Pwned Passwords"):
                return reto_patrones(demo=True)
            return
        resultados.append((clave, veces))
        etiqueta = miles(veces) if veces else "0 (no aparece)"
        print("     {:<18}{:>18}".format(clave, etiqueta))
    frase = "-".join(secrets.choice(["coche", "nube", "verde", "rio", "gato", "sol"]) for _ in range(4))
    print("\n  " + NEGRITA + "Frase larga generada al azar: " + FIN + frase)
    v = DEMO_PATRONES.get("frase", 0) if demo else veces_filtrada(frase)
    print("     Veces filtrada: " + (miles(v) if v and v > 0 else "0 (no aparece)"))
    print(GRIS + "\n  Fuente: Have I Been Pwned · Pwned Passwords" + FIN)

    preguntar("Reto 8 · Patrones de contraseñas", [
        "Ordena mentalmente las contraseñas de más a menos filtrada. ¿Qué tienen en común las más filtradas?",
        "'Madrid2024!' parece fuerte (mayúscula, número, símbolo) pero suele estar muy filtrada. ¿Por qué no basta con esa 'complejidad'?",
        "Compara las contraseñas con la frase larga generada al azar. ¿Qué hace que una contraseña sea difícil de encontrar en estas listas?",
    ])


def reto_caso(demo=False):
    titulo("9 · Caso integrador: informe exprés de una organización")
    print("  Reúne lo aprendido: huella del dominio (reto 7) y contexto de brechas (reto 6).")
    print("  Al final redactarás tú el informe, separando observación e inferencia.\n")
    reto_huella(demo)
    print("\n" + GRIS + "  ── Ahora el contexto general de las filtraciones ──" + FIN)
    catalogo, origen = catalogo_brechas(demo)
    if catalogo:
        stealer = sum(1 for b in catalogo if b.get("IsStealerLog"))
        observacion("En el catálogo hay " + miles(len(catalogo)) + " brechas; "
                    + miles(stealer) + " son logs de infostealers.")
    preguntar("Reto 9 · Caso integrador", [
        "Con los subdominios y el correo del dominio, escribe 2 OBSERVACIONES (solo hechos vistos).",
        "Escribe 1 INFERENCIA que se apoye en esas observaciones, y marca qué habría que VERIFICAR.",
        "Si encontraras este dominio en un canal de filtraciones, ¿qué comprobarías primero y por qué? Recuerda el límite legal del art. 197.3 del Código Penal.",
    ])


def modo_demo():
    titulo("4 · MODO DEMOSTRACIÓN (sin Internet · datos ficticios)")
    print("  Se ejecutan las tres consultas con datos inventados para ver el resultado.")
    input("  Pulsa Intro para empezar…")
    consultar_correo(demo=True)
    input("\n  Pulsa Intro para continuar…")
    consultar_contrasena(demo=True)
    input("\n  Pulsa Intro para continuar…")
    consultar_dominio(demo=True)


# ============================================= preparación del docente (caché)
def preparar(dominio):
    """Descarga por adelantado el catálogo de brechas y los certificados de un dominio."""
    titulo("MODO PREPARACIÓN DEL DOCENTE")
    print("  Descargando datos para dejarlos en la carpeta 'cache'.\n")
    catalogo, origen = catalogo_brechas(False)
    print(("  ✔ Catálogo de brechas: " + miles(len(catalogo)) + " registros.") if catalogo
          else "  ✗ No se pudo descargar el catálogo de brechas.")
    if dominio:
        dominio = limpiar_dominio(dominio)
        registros, _ = certificados_dominio(dominio, False)
        print(("  ✔ Certificados de " + dominio + ": " + miles(len(registros)) + " registros.")
              if registros is not None else "  ✗ No se pudieron descargar los certificados.")
    print("\n  Copia la carpeta 'cache' junto al script de cada alumno.")
    print("  Los retos 5, 6, 7 y 9 funcionarán sin depender de la red en clase.\n")


# ===================================================================== menú
def main():
    global ALUMNO
    titulo("OCC · M2.12 Leaks · Práctica guiada  (v" + VERSION + ")")
    print("  Uso exclusivamente docente. Consulta solo datos propios o de prueba.")
    try:
        ALUMNO = input("\n  Escribe tu nombre (para el informe) y pulsa Intro: ").strip()
    except EOFError:
        ALUMNO = ""
    opciones = {"1": consultar_correo, "2": consultar_contrasena, "3": consultar_dominio,
                "4": modo_demo, "5": reto_anatomia, "6": reto_tendencias,
                "7": reto_huella, "8": reto_patrones, "9": reto_caso}
    while True:
        print("\n" + NEGRITA + "  ¿Qué quieres hacer?" + FIN)
        print(GRIS + "  — Consultas básicas —" + FIN)
        print("   1) Comprobar un CORREO en filtraciones")
        print("   2) Comprobar una CONTRASEÑA (sin enviarla)")
        print("   3) Ver los SUBDOMINIOS de un dominio")
        print("   4) Modo DEMOSTRACIÓN (sin Internet)")
        print(GRIS + "  — Retos de análisis (tú interpretas los datos) —" + FIN)
        print("   5) Anatomía de una brecha")
        print("   6) Tendencias de las filtraciones")
        print("   7) Huella pública de un dominio")
        print("   8) Patrones de contraseñas")
        print("   9) Caso integrador")
        print("   0) Salir")
        try:
            eleccion = input("\n  Escribe un número y pulsa Intro: ").strip()
        except EOFError:
            eleccion = "0"
        if eleccion == "0":
            if os.path.exists(INFORME):
                print(VERDE + "\n  Tu informe está en: " + FIN + INFORME)
            print("  ¡Hasta la próxima!\n")
            return
        if eleccion in opciones:
            opciones[eleccion]()
        else:
            aviso("Opción no válida. Escribe un número del 0 al 9.")


if __name__ == "__main__":
    try:
        if len(sys.argv) >= 2 and sys.argv[1] == "--preparar":
            preparar(sys.argv[2] if len(sys.argv) >= 3 else "")
        else:
            main()
    except KeyboardInterrupt:
        print("\n  Práctica interrumpida. ¡Hasta la próxima!\n")
