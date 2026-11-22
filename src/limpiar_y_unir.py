"""Limpia las bases de data/raw y genera data/processed/panel_publico.csv (tabla mensual).

Uso (desde la raíz del repo):  python src/limpiar_y_unir.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, PROC = ROOT / "data" / "raw", ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
LOG = []


def log(msg):
    print(msg)
    LOG.append(msg)


def periodo_a_fecha(serie):
    """202209 -> Timestamp 2022-09-01 (año-mes)."""
    return pd.to_datetime(serie.astype(str), format="%Y%m")


# 4) Tráfico ANI (peajes elegidos) ----------------------------------------------
# Elegidos: LAS PALMAS y GUARNE. Son los peajes de la ruta Medellín - Oriente
# antioqueño / aeropuerto José María Córdova (Rionegro), el principal acceso de
# turistas y asistentes a eventos; ambos tienen serie completa, sin duplicados,
# de 2014-01 a 2026-05. (Elección propia: confirmar con el equipo.)
PEAJES = ["LAS PALMAS", "GUARNE"]


def limpiar_trafico():
    d = pd.read_csv(RAW / "trafico_ani.csv", dtype=str, low_memory=False)
    n0 = len(d)
    d = d[d["Peaje"].isin(PEAJES)].copy()
    d["mes"] = pd.to_datetime(d["Desde"], format="%Y %b %d %I:%M:%S %p").dt.to_period("M").dt.to_timestamp()
    d["trafico"] = pd.to_numeric(d["CantidadTrafico"].str.replace(",", ""), errors="coerce")
    d = d.drop_duplicates(["IdPeaje", "CategoriaTarifa", "mes"])
    total = d.pivot_table(index="mes", columns="Peaje", values="trafico", aggfunc="sum")
    total.columns = [f"trafico_{c.lower().replace(' ', '_')}" for c in total.columns]
    total["trafico_total"] = total.sum(axis=1, min_count=1)
    livianos = d[d["CategoriaTarifa"] == "I"].groupby("mes")["trafico"].sum().rename("trafico_livianos")
    out = total.join(livianos).reset_index()
    log(f"trafico ANI: {n0} filas crudas ({len(PEAJES)} peajes elegidos) -> {len(out)} meses ({out.mes.min():%Y-%m} a {out.mes.max():%Y-%m})")
    return out


# 5) DANE EMA: ocupación (%) e índice de tarifas, región Antioquia ---------------
# OJO: es Antioquia (no solo Medellín) y la tarifa es un ÍNDICE (base 2019=100), no pesos.
MESES = {m: i + 1 for i, m in enumerate(["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                                         "agosto", "septiembre", "octubre", "noviembre", "diciembre"])}


def _hoja_ema(hoja, columnas):
    """Lee una hoja del anexo EMA: años en col 0 (se rellenan hacia abajo), meses en col 1."""
    d = pd.read_excel(RAW / "ema_anexos_sep2026.xlsx", sheet_name=hoja, header=None)
    d = d.iloc[12:, :].copy()
    # los años desde 2023 vienen como "2023p" (p = provisional): se extraen los 4 dígitos
    d[0] = pd.to_numeric(d[0].astype(str).str.extract(r"(\d{4})")[0], errors="coerce").ffill()
    d["_m"] = d[1].astype(str).str.strip().str.lower().map(MESES)
    d = d.dropna(subset=[0, "_m"])
    out = pd.DataFrame({"mes": pd.to_datetime(dict(year=d[0].astype(int), month=d["_m"].astype(int), day=1))})
    for nombre, col in columnas.items():
        out[nombre] = pd.to_numeric(d[col], errors="coerce").values
    return out


def limpiar_ema():
    ocu = _hoja_ema("4.2 Porc Mens Ocupación.reg", {"ocupacion_ema_antioquia": 8})
    tar = _hoja_ema("6.1 Ind.Var Tarifas.acomoda", {"indice_tarifa_ema_sencilla": 38, "indice_tarifa_ema_doble": 41})
    out = ocu.merge(tar, on="mes", how="outer").sort_values("mes")
    out["indice_tarifa_ema_antioquia"] = out[["indice_tarifa_ema_sencilla", "indice_tarifa_ema_doble"]].mean(axis=1)
    log(f"EMA Antioquia: {len(out)} meses ({out.mes.min():%Y-%m} a {out.mes.max():%Y-%m})")
    return out


# 6) Migración Colombia: entradas de extranjeros por el Aeropuerto José María Córdova ---
# El archivo no trae el nombre del puesto, solo sus coordenadas ("Ubicación PCM").
# Las del aeropuerto JMC (Rionegro) son (6.1716,-75.4275) y una variante (6.1713,-75.4272).
JMC = ("(6.171601,-75.427454)", "(6.17134,-75.427194)")


def limpiar_migracion():
    d = pd.read_csv(RAW / "migracion_entradas_extranjeros.csv", dtype=str, low_memory=False)
    n0 = len(d)
    d = d[d["Ubicación PCM"].isin(JMC)].copy()
    d["Total"] = pd.to_numeric(d["Total"].str.replace(",", ""), errors="coerce")
    d["mes"] = pd.to_datetime(dict(year=d["Año"].astype(int),
                                   month=d["Mes"].str.strip().str.lower().map(MESES), day=1))
    out = d.groupby("mes", as_index=False)["Total"].sum().rename(columns={"Total": "entradas_extranjeros_jmc"})
    log(f"migracion: {n0} filas -> {len(d)} del aeropuerto JMC -> {len(out)} meses ({out.mes.min():%Y-%m} a {out.mes.max():%Y-%m})")
    return out


PERIODO = ("2019-01", "2025-12")  # periodo pedido por el equipo


def main():
    bases = {
        "trafico": limpiar_trafico(),
        "ema": limpiar_ema(),
        "migracion": limpiar_migracion(),
    }
    for nombre, df in bases.items():
        df.to_csv(PROC / f"{nombre}_limpio.csv", index=False)

    # Unión mensual: calendario completo desde el primer hasta el último mes con dato
    todos = pd.concat([b["mes"] for b in bases.values()])
    panel = pd.DataFrame({"mes": pd.date_range(todos.min(), todos.max(), freq="MS")})
    for df in bases.values():
        panel = panel.merge(df, on="mes", how="left")
    panel = panel[(panel["mes"] >= pd.Timestamp(PERIODO[0])) & (panel["mes"] <= pd.Timestamp(PERIODO[1]) + pd.offsets.MonthBegin(0))].reset_index(drop=True)
    panel.insert(1, "anio", panel["mes"].dt.year)
    panel.insert(2, "mes_num", panel["mes"].dt.month)
    panel["mes"] = panel["mes"].dt.strftime("%Y-%m")
    panel.to_csv(PROC / "panel_publico.csv", index=False)

    # Verificación de la unión
    log(f"\n== VERIFICACIÓN DE LA UNIÓN (panel limitado a {PERIODO[0]} - {PERIODO[1]}) ==")
    log(f"panel_publico: {len(panel)} filas (meses) x {panel.shape[1]} columnas; mes duplicados: {int(panel['mes'].duplicated().sum())}")
    for nombre, df in bases.items():
        en_periodo = df[(df["mes"] >= pd.Timestamp(PERIODO[0])) & (df["mes"] <= pd.Timestamp("2025-12-01"))]
        cruzan = en_periodo["mes"].dt.strftime("%Y-%m").isin(panel["mes"]).sum()
        log(f"  {nombre}: {len(df)} meses en la base ({len(en_periodo)} dentro de {PERIODO[0]} a {PERIODO[1]}), {cruzan} cruzaron con el panel")
    cols = {"trafico": "trafico_total", "ema": "ocupacion_ema_antioquia",
            "migracion": "entradas_extranjeros_jmc"}
    for nombre, c in cols.items():
        sin = panel.loc[panel[c].isna(), "mes"]
        log(f"  meses sin dato de {nombre} ({c}): {len(sin)}"
            + (f" -> de {sin.iloc[0]} a {sin.iloc[-1]}" if len(sin) else ""))
    comun = panel.dropna(subset=list(cols.values()))
    log(f"  periodo con las 3 bases a la vez: {comun['mes'].min()} a {comun['mes'].max()} ({len(comun)} meses)")
    (PROC / "verificacion_union.txt").write_text("\n".join(LOG), encoding="utf-8")


if __name__ == "__main__":
    main()
