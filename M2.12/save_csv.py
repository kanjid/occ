#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
save_csv.py
Lee correlated.json y genera un CSV de informe con columnas relevantes.
"""

import os
import sys
import json
import csv
import argparse
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def safe_get(d, *keys, default=""):
    cur = d
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur

def flatten_record(rec):
    """
    Produce una lista de filas para el CSV a partir de un registro correlacionado.
    Si hay múltiples emails/domains, genera varias filas.
    """
    rows = []
    ts = rec.get("ts", "")
    src_from = rec.get("from", "")
    src_to = rec.get("to", "")
    snippet = (rec.get("body") or "")[:300].replace("\n", " ")

    emails = rec.get("emails", [])  # lista de dicts con 'email' key
    domains = rec.get("domains", [])  # lista de dicts

    # Si hay emails, prioriza filas por email
    if emails:
        for e in emails:
            email = e.get("email", "") if isinstance(e, dict) else (e or "")
            email_hash = rec.get("emails_hash", [])
            # try to guess hash for this email (best-effort)
            email_hash_val = ""
            if isinstance(rec.get("emails_hash", None), list):
                # try match by position
                try:
                    idx = [ee.get("email","") for ee in emails].index(email)
                    email_hash_val = rec["emails_hash"][idx] if idx < len(rec["emails_hash"]) else ""
                except Exception:
                    email_hash_val = ""
            hunter_ok = "no"
            if isinstance(e, dict) and e.get("hunter_verifier"):
                hunter_ok = "yes"
            rows.append({
                "ts": ts, "from": src_from, "to": src_to, "type": "email",
                "entity": email, "entity_hash": email_hash_val,
                "hunter_ok": hunter_ok,
                "urlscan_hits": "",
                "notes": e.get("note","") if isinstance(e, dict) else ""
            })
    # If no emails but domains exist, produce rows for domains
    if not emails and domains:
        for d in domains:
            domain = d.get("domain") if isinstance(d, dict) else d
            urlscan_hits = ""
            notes = ";".join(d.get("note", [])) if isinstance(d, dict) else ""
            if isinstance(d, dict) and d.get("urlscan") and isinstance(d["urlscan"], dict) and d["urlscan"].get("ok"):
                # count results if available
                try:
                    urlscan_hits = len(d["urlscan"]["data"].get("results", []))
                except Exception:
                    urlscan_hits = ""
            rows.append({
                "ts": ts, "from": src_from, "to": src_to, "type": "domain",
                "entity": domain, "entity_hash": "",
                "hunter_ok": "yes" if isinstance(d.get("hunter"), dict) and d["hunter"].get("ok") else "no",
                "urlscan_hits": urlscan_hits,
                "notes": notes
            })
    # If neither emails nor domains, create a generic row
    if not emails and not domains:
        rows.append({
            "ts": ts, "from": src_from, "to": src_to, "type": "other",
            "entity": "", "entity_hash": "", "hunter_ok": "", "urlscan_hits": "", "notes": ""
        })
    # attach snippet to each row
    for r in rows:
        r["snippet"] = snippet
    return rows

def cmd_save(args):
    src = args.input or "correlated.json"
    if not os.path.exists(src):
        logging.error("No existe %s. Ejecuta correlate primero.", src); sys.exit(1)
    with open(src, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    rows = []
    for rec in data:
        try:
            rows.extend(flatten_record(rec))
        except Exception as e:
            logging.warning("Error procesando registro: %s", e)

    if not rows:
        logging.info("No hay filas para escribir.")
        return

    out = args.output or f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    fieldnames = ["ts","from","to","type","entity","entity_hash","hunter_ok","urlscan_hits","notes","snippet"]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    logging.info("CSV guardado: %s (filas: %d)", out, len(rows))

def main():
    ap = argparse.ArgumentParser(description="Save correlated JSON as CSV report")
    ap.add_argument("--input", "-i", help="correlated.json file", default="correlated.json")
    ap.add_argument("--output", "-o", help="CSV output file", default=None)
    args = ap.parse_args()
    cmd_save(args)

if __name__ == "__main__":
    main()
