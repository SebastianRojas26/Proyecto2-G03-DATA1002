# Limpieza e integración de las bases públicas -> data/processed/panel_publico.csv
# Uso (desde la raíz del repo): python src/limpiar_y_unir.py

import pandas as pd

RAW = "data/raw/"
PROC = "data/processed/"

meses = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
         "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}

# Tráfico ANI
ani = pd.read_csv(RAW + "trafico_ani.csv", dtype=str)
ani = ani[ani["Peaje"].isin(["LAS PALMAS", "GUARNE"])].copy()

ani["mes"] = pd.to_datetime(ani["Desde"], format="%Y %b %d %I:%M:%S %p")
ani["trafico"] = pd.to_numeric(ani["CantidadTrafico"].str.replace(",", ""), errors="coerce")
ani = ani.drop_duplicates(["IdPeaje", "CategoriaTarifa", "mes"])

trafico = ani.pivot_table(index="mes", columns="Peaje", values="trafico", aggfunc="sum")
trafico.columns = ["trafico_guarne", "trafico_las_palmas"]
trafico["trafico_total"] = trafico["trafico_guarne"] + trafico["trafico_las_palmas"]
trafico["trafico_livianos"] = ani[ani["CategoriaTarifa"] == "I"].groupby("mes")["trafico"].sum()
trafico = trafico.reset_index()

# DANE EMA (Antioquia)
archivo = RAW + "ema_anexos_sep2026.xlsx"


def leer_hoja_ema(hoja, columnas):
    d = pd.read_excel(archivo, sheet_name=hoja, header=None).iloc[12:, :].copy()
    # el año viene solo en enero y desde 2023 como "2023p"
    d["anio"] = pd.to_numeric(d[0].astype(str).str.extract(r"(\d{4})")[0]).ffill()
    d["mes_num"] = d[1].astype(str).str.strip().str.lower().map(meses)
    d = d.dropna(subset=["anio", "mes_num"])
    out = pd.DataFrame({"mes": pd.to_datetime(dict(year=d["anio"].astype(int),
                                                   month=d["mes_num"].astype(int), day=1))})
    for nombre, col in columnas.items():
        out[nombre] = pd.to_numeric(d[col], errors="coerce").values
    return out


ocupacion = leer_hoja_ema("4.2 Porc Mens Ocupación.reg", {"ocupacion_ema_antioquia": 8})
tarifas = leer_hoja_ema("6.1 Ind.Var Tarifas.acomoda",
                        {"indice_tarifa_ema_sencilla": 38, "indice_tarifa_ema_doble": 41})
tarifas["indice_tarifa_ema_antioquia"] = tarifas[["indice_tarifa_ema_sencilla",
                                                  "indice_tarifa_ema_doble"]].mean(axis=1)
ema = ocupacion.merge(tarifas, on="mes", how="outer")

# Migración Colombia (aeropuerto José María Córdova)
mig = pd.read_csv(RAW + "migracion_entradas_extranjeros.csv", dtype=str)
mig = mig[mig["Ubicación PCM"].isin(["(6.171601,-75.427454)", "(6.17134,-75.427194)"])].copy()

mig["Total"] = pd.to_numeric(mig["Total"].str.replace(",", ""), errors="coerce")
mig["mes_num"] = mig["Mes"].str.strip().str.lower().map(meses)
mig["mes"] = pd.to_datetime(dict(year=mig["Año"].astype(int), month=mig["mes_num"], day=1))

migracion = mig.groupby("mes", as_index=False)["Total"].sum()
migracion = migracion.rename(columns={"Total": "entradas_extranjeros_jmc"})

# Unión mensual 2019-01 a 2025-12
panel = pd.DataFrame({"mes": pd.date_range("2019-01-01", "2025-12-01", freq="MS")})
for base in [trafico, ema, migracion]:
    panel = panel.merge(base, on="mes", how="left")

panel.insert(1, "anio", panel["mes"].dt.year)
panel.insert(2, "mes_num", panel["mes"].dt.month)
panel["mes"] = panel["mes"].dt.strftime("%Y-%m")

# Verificación
inicio, fin = pd.Timestamp("2019-01-01"), pd.Timestamp("2025-12-01")
for nombre, base in {"tráfico ANI": trafico, "EMA": ema, "migración": migracion}.items():
    en_periodo = base[(base["mes"] >= inicio) & (base["mes"] <= fin)]
    cruzan = en_periodo["mes"].dt.strftime("%Y-%m").isin(panel["mes"]).sum()
    print(f"{nombre}: {len(base)} meses en la base, {len(en_periodo)} en 2019-2025, {cruzan} cruzaron")
print("Filas del panel:", len(panel), "| columnas:", panel.shape[1])
print("Meses duplicados:", panel["mes"].duplicated().sum())
print("Valores faltantes:", panel.isna().sum().sum())

panel.to_csv(PROC + "panel_publico.csv", index=False)
