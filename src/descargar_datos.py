"""Descarga las bases de datos.gov.co SIN modificarlas a data/raw.

Uso (desde la raíz del repo):  python src/descargar_datos.py
Usa la API de exportación CSV de Socrata (completa, sin límite de filas).
"""
from pathlib import Path
import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

BASES = {
    "trafico_ani": "8yi9-t44c",                    # Tráfico vehicular ANI
    "migracion_entradas_extranjeros": "96sh-4v8d", # Migración Colombia: entradas de extranjeros
}
# DANE EMA (Excel): descargar a mano de
# https://www.dane.gov.co/files/operaciones/EMA/anex-EMA-sep2026.xlsx  -> data/raw/ema_anexos_sep2026.xlsx


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for nombre, dataset_id in BASES.items():
        url = f"https://www.datos.gov.co/api/views/{dataset_id}/rows.csv?accessType=DOWNLOAD"
        destino = RAW / f"{nombre}.csv"
        print(f"Descargando {nombre} ({dataset_id}) ...")
        with requests.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(destino, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    f.write(chunk)
        print(f"  -> {destino} ({destino.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
