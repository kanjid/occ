# analyst.py

import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import matplotlib.pyplot as plt

# ==== Config ====
INPUT_FILE = "mensajes_enriquecidos.json"  # cambia si usas otro nombre
KEYWORDS = ["hack", "vpn", "exploit"]      # palabras clave a buscar (minúsculas)
OUT_COUNT_CSV = "reporte_conteo_claves.csv"
OUT_DOMAINS_CSV = "reporte_top_dominios.csv"
# ================

def load_json_or_jsonl(path: Path):
    """
    Detecta si el archivo es JSON (lista) o JSONL (json por línea) y lo carga.
    Devuelve una lista de dicts.
    """
    with path.open("r", encoding="utf-8") as f:
        head = f.read(2048)
        f.seek(0)
        # Si empieza con '[' asumimos JSON de lista
        if head.lstrip().startswith("["):
            return json.load(f)
        else:
            data = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data.append(json.loads(line))
            return data

def clean_url(u: str) -> str:
    """
    Limpia URL de caracteres de cierre comunes y espacios.
    """
    if not u:
        return u
    u = u.strip()
    # Quitar cierres comunes que a menudo quedan pegados
    while len(u) > 0 and u[-1] in "]}).,>":
        u = u[:-1]
    # También quitar comillas si las hay
    u = u.strip('\'"')
    return u

def url_to_domain(u: str) -> str | None:
    try:
        parsed = urlparse(u)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host or None
    except Exception:
        return None

def extract_urls_from_text(text: str) -> list[str]:
    URL_RE = re.compile(r'https?://\S+', re.IGNORECASE)
    return [clean_url(m) for m in URL_RE.findall(text or "")]

def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Asegurar columnas que usamos
    for col in ("texto", "links", "date"):
        if col not in df.columns:
            df[col] = None
    return df

def main():
    path = Path(INPUT_FILE)
    if not path.exists():
        print(f"❌ No se encontró el archivo: {path.resolve()}")
        sys.exit(1)

    # 1) Cargar datos (JSON lista o JSONL)
    registros = load_json_or_jsonl(path)
    if not isinstance(registros, list):
        print("❌ Formato inesperado: se esperaba lista de objetos.")
        sys.exit(1)

    df = pd.DataFrame(registros)
    df = ensure_columns(df)

    # Normalizar columnas básicas
    df["texto"] = df["texto"].fillna("")
    # 'links' puede venir ya como lista en tu JSON enriquecido
    df["links"] = df["links"].apply(lambda x: x if isinstance(x, list) else [])

    # 2) Conteo por palabra clave
    def etiqueta(texto: str):
        t = (texto or "").lower()
        return [k for k in KEYWORDS if k in t]

    df["keys"] = df["texto"].apply(etiqueta)
    exploded = df.explode("keys").dropna(subset=["keys"])
    conteo_claves = exploded["keys"].value_counts().sort_values(ascending=False)

    # 3) Actividad por hora (usando 'date' ISO8601 si existe)
    actividad = pd.Series(dtype="int64")
    if df["date"].notna().any():
        # Parsear a datetime (maneja zona horaria)
        df["_ts"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
        ts_df = df.dropna(subset=["_ts"]).set_index("_ts")
        if not ts_df.empty:
            # Conteo por hora
            actividad = ts_df.resample("h").size()

    # 4) Extraer URLs y dominios TOP
    # URLs provenientes del campo 'links'
    urls_from_field = sum(df["links"].tolist(), [])
    # URLs detectadas en texto
    urls_from_text = sum(df["texto"].apply(extract_urls_from_text).tolist(), [])
    urls_all = [clean_url(u) for u in (urls_from_field + urls_from_text) if u]

    # Filtrar URLs obviamente inválidas
    urls_all = [u for u in urls_all if u.lower().startswith(("http://", "https://"))]

    dominios = [d for d in (url_to_domain(u) for u in urls_all) if d]
    top_dominios_cnt = Counter(dominios).most_common(10)

    # 5) Mostrar resultados y exportar
    print("\n=== Conteo por palabra clave ===")
    if not conteo_claves.empty:
        print(conteo_claves.to_string())
        conteo_claves.to_csv(OUT_COUNT_CSV, header=["occurrences"])
        print(f"💾 Guardado: {OUT_COUNT_CSV}")
    else:
        print("(sin coincidencias)")

    print("\n=== TOP dominios (top 10) ===")
    if top_dominios_cnt:
        for dom, c in top_dominios_cnt:
            print(f"{dom}: {c}")
        pd.DataFrame(top_dominios_cnt, columns=["domain", "occurrences"]).to_csv(OUT_DOMAINS_CSV, index=False)
        print(f"💾 Guardado: {OUT_DOMAINS_CSV}")
    else:
        print("(sin dominios detectados)")

    # Gráfico 1: barras por palabra clave
    if not conteo_claves.empty:
        plt.figure()
        conteo_claves.plot(kind="bar")
        plt.title("Alertas por palabra clave")
        plt.xlabel("Palabra clave")
        plt.ylabel("Ocurrencias")
        plt.tight_layout()
        plt.show()
    else:
        print("\n(⚠️ No hay datos para el gráfico de palabras clave)")

    # Gráfico 2: actividad por hora
    if not actividad.empty:
        plt.figure()
        actividad.plot(kind="line")
        plt.title("Actividad por hora")
        plt.xlabel("Hora (UTC)")
        plt.ylabel("Mensajes")
        plt.tight_layout()
        plt.show()
    else:
        print("\n(⚠️ No hay timestamps válidos para el gráfico de actividad)")

if __name__ == "__main__":
    main()
