#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
correlate_osint.py (versión limitada)
Realiza correlación de entidades (emails y dominios) con Hunter.io y URLScan.io
Usa un límite opcional (--limit) para controlar el número de registros analizados.
"""

import os
import sys
import time
import json
import argparse
import logging
import hashlib
import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Cargar variables del archivo .env
load_dotenv()

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
URLSCAN_API_KEY = os.getenv("URLSCAN_API_KEY")
HUNTER_DELAY = float(os.getenv("HUNTER_DELAY", "0.5"))
URLSCAN_DELAY = float(os.getenv("URLSCAN_DELAY", "0.2"))
REQUEST_TIMEOUT = 12

session = requests.Session()
session.headers.update({"User-Agent": "OSINT-Course/1.0 (+https://example.local)"})


# === Funciones auxiliares ===

def sha256(s):
    try:
        return hashlib.sha256(s.encode("utf-8")).hexdigest()
    except Exception:
        return ""


def query_hunter_email(email):
    """Verifica un correo con Hunter.io"""
    if not HUNTER_API_KEY:
        return {"ok": False, "note": "no_hunter_key"}
    url = "https://api.hunter.io/v2/email-verifier"
    params = {"email": email, "api_key": HUNTER_API_KEY}
    try:
        r = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        return {"ok": False, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def query_urlscan(domain):
    """Consulta dominio en URLScan.io"""
    url = "https://urlscan.io/api/v1/search/"
    params = {"q": f"domain:{domain}"}
    headers = {"API-Key": URLSCAN_API_KEY} if URLSCAN_API_KEY else {}
    try:
        r = session.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        return {"ok": False, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def correlate_record(rec):
    """Procesa un registro individual"""
    out = {
        "ts": rec.get("ts"),
        "from": rec.get("from"),
        "to": rec.get("to"),
        "emails": [],
        "domains": []
    }

    # Procesar emails
    for e in rec.get("emails", []):
        entry = {"email": e, "hash": sha256(e)}
        if HUNTER_API_KEY:
            res = query_hunter_email(e)
            entry["hunter"] = res
            entry["note"] = "ok" if res.get("ok") else "error"
            time.sleep(HUNTER_DELAY)
        else:
            entry["note"] = "skipped"
        out["emails"].append(entry)

    # Procesar dominios
    for d in rec.get("domains", []):
        entry = {"domain": d}
        res = query_urlscan(d)
        entry["urlscan"] = res
        entry["note"] = "ok" if res.get("ok") else "error"
        time.sleep(URLSCAN_DELAY)
        out["domains"].append(entry)

    return out


def main():
    parser = argparse.ArgumentParser(description="Correlación limitada con Hunter.io y URLScan.io")
    parser.add_argument("--input", "-i", default="entities.json", help="Archivo de entrada (entities.json)")
    parser.add_argument("--output", "-o", default="correlated.json", help="Archivo de salida (correlated.json)")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Número máximo de registros a correlacionar")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        logging.error("Archivo no encontrado: %s", args.input)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    total = len(data)
    limit = min(args.limit, total)
    logging.info(f"Procesando {limit} de {total} registros...")

    correlated = []
    for i, rec in enumerate(data[:limit], 1):
        try:
            correlated.append(correlate_record(rec))
            logging.info(f"Registro {i}/{limit} procesado correctamente.")
        except Exception as e:
            logging.warning(f"Error en registro {i}: {e}")

    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(correlated, fh, indent=2, ensure_ascii=False)

    logging.info(f"Correlación finalizada. Archivo generado: {args.output}")


if __name__ == "__main__":
    main()
