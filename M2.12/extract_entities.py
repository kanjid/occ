#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_entities.py
Extrae entidades (emails, phones, urls, domains, mentions) de un JSON/CSV de mensajes.
Salida: entities.json
"""

import os
import sys
import json
import csv
import argparse
import logging
from io import StringIO

from email_validator import validate_email, EmailNotValidError
import phonenumbers
from urlextract import URLExtract
import tldextract
from datetime import datetime
from dateutil import parser as dateparser

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

extractor = URLExtract()
# Avoid fetching suffix list online for speed/reproducibility
tldx = tldextract.TLDExtract(suffix_list_urls=None)

def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        obj = json.load(fh)
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict) and "messages" in obj:
        return obj["messages"]
    return [obj]

def sniff_delimiter(sample_text):
    return ";" if sample_text.count(";") > sample_text.count(",") else ","

def load_csv(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        raw = fh.read()
    delim = sniff_delimiter(raw[:5000])
    reader = csv.reader(StringIO(raw), delimiter=delim)
    rows = list(reader)
    if not rows:
        return []
    header = None
    candidate = rows[0]
    hdr_join = " ".join([str(x).lower() for x in candidate])
    looks_header = any(k in hdr_join for k in ["email","from","to","body","ts","date"])
    data = []
    if looks_header:
        header = [h.strip() for h in candidate]
        for r in rows[1:]:
            rec = {header[i]: (r[i] if i < len(r) else "") for i in range(len(header))}
            data.append(rec)
    else:
        for r in rows:
            rec = {f"c{i}": r[i] for i in range(len(r))}
            data.append(rec)
    return data

def normalize_ts(ts):
    if not ts:
        return ""
    try:
        return dateparser.isoparse(str(ts)).isoformat()
    except Exception:
        try:
            return dateparser.parse(str(ts)).isoformat()
        except Exception:
            return str(ts)

def find_emails(tokens):
    out, seen = [], set()
    for t in tokens:
        cand = t.strip(".,;:()[]{}<>\"'")
        if "@" not in cand:
            continue
        try:
            v = validate_email(cand, check_deliverability=False)
            email = v.normalized
            if email not in seen:
                seen.add(email); out.append(email)
        except EmailNotValidError:
            continue
    return out

def find_phones(text, region="ES"):
    out, seen = [], set()
    try:
        for m in phonenumbers.PhoneNumberMatcher(str(text), region):
            formatted = phonenumbers.format_number(m.number, phonenumbers.PhoneNumberFormat.E164)
            if formatted not in seen:
                seen.add(formatted); out.append(formatted)
    except Exception:
        pass
    return out

def find_urls_and_domains(text):
    out_urls, out_domains, seen_urls, seen_domains = [], [], set(), set()
    try:
        urls = extractor.find_urls(str(text))
    except Exception:
        urls = []
    for u in urls:
        u = u.strip()
        if u and u not in seen_urls:
            seen_urls.add(u); out_urls.append(u)
        try:
            ext = tldx(u)
            rd = ext.registered_domain
            if rd and rd not in seen_domains:
                seen_domains.add(rd); out_domains.append(rd)
        except Exception:
            continue
    return out_urls, out_domains

def find_mentions(text):
    out, seen = [], set()
    for tok in str(text).replace("\n", " ").split():
        if tok.startswith("@") and len(tok) > 1:
            m = tok.strip(".,;:()[]{}<>\"'")
            if m not in seen:
                seen.add(m); out.append(m)
    return out

def extract_from_record(rec):
    # Support different field names
    ts = rec.get("ts") or rec.get("date") or rec.get("created_at") or ""
    sender = rec.get("from") or rec.get("sender") or rec.get("email") or ""
    to = rec.get("to") or rec.get("channel") or rec.get("canal") or ""
    body = rec.get("body") or rec.get("text") or ""
    if not body:
        # fallback: join other string fields
        parts = []
        for k,v in rec.items():
            if k.lower() in ("ts","from","to"):
                continue
            if isinstance(v, str) and v.strip():
                parts.append(f"{k}:{v}")
        body = " | ".join(parts)[:2000]

    ts = normalize_ts(ts)
    words = str(body).replace("\n", " ").split()

    emails = find_emails(words)
    phones = find_phones(body)
    urls, domains = find_urls_and_domains(body)
    mentions = find_mentions(body)

    return {
        "ts": ts,
        "from": sender,
        "to": to,
        "body": body,
        "emails": emails,
        "phones": phones,
        "urls": urls,
        "domains": domains,
        "mentions": mentions
    }

def cmd_extract(args):
    path = args.input
    if not os.path.exists(path):
        logging.error("No existe: %s", path); sys.exit(1)
    data = load_json(path) if path.lower().endswith(".json") else load_csv(path)
    logging.info("Registros cargados: %d", len(data))
    extracted = [extract_from_record(r) for r in data]
    out = args.output or "entities.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(extracted, fh, indent=2, ensure_ascii=False)
    logging.info("Entidades extraídas guardadas en: %s (registros: %d)", out, len(extracted))

def main():
    ap = argparse.ArgumentParser(description="Extract entities from leak JSON/CSV")
    ap.add_argument("--input", "-i", required=True, help="Input file (JSON or CSV/TXT)")
    ap.add_argument("--output", "-o", default="entities.json", help="Output entities JSON")
    args = ap.parse_args()
    cmd_extract(args)

if __name__ == "__main__":
    main()
