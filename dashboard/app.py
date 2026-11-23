import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")
df = pd.read_csv("data/processed/panel_final.csv")
df["fecha"] = pd.to_datetime(df["mes"], format="%Y-%m")
df["temporada"] = np.where(df["temporada_alta"] == 1, "Alta", "Baja")
df["evento"] = np.where(df["hay_evento_grande"] == 1, "Con evento grande", "Sin evento grande")
df["periodo"] = np.where(df["covid"] == 1, "COVID", "Normal")

INDICADORES = {
    "Ocupación hotelera (%, Antioquia)": "ocupacion_ema_antioquia",
    "Índice de tarifa (base 2019=100)": "indice_tarifa_ema_antioquia",
    "Entradas de extranjeros (aeropuerto JMC)": "entradas_extranjeros_jmc",
    "Tráfico vehicular (Las Palmas + Guarne)": "trafico_total",
}

st.title("Conciertos, festivales y turismo en Medellín")
st.caption("Elaborado con el panel mensual del proyecto (panel_final.csv)")
st.markdown("**Pregunta analítica:** Entre 2019 y 2025, ¿Los meses con grandes conciertos y festivales en Medellín se asocian con un incremento en la actividad turística de la región?")

# Filtros 
st.sidebar.header("FILTROS")
filtro_anio = st.sidebar.multiselect(label="AÑO",
                                     options=sorted(df.anio.unique()),
                                     default=sorted(df.anio.unique()))
filtro_temporada = st.sidebar.multiselect(label="TEMPORADA",
                                          options=["Alta", "Baja"],
                                          default=["Alta", "Baja"])
filtro_periodo = st.sidebar.multiselect(label="PERIODO",
                                        options=["Normal", "COVID"],
                                        default=["Normal"])
ind_nombre = st.sidebar.selectbox(label="INDICADOR TURÍSTICO", options=list(INDICADORES))
umbral = st.sidebar.selectbox(label="MARCAR MESES CON AL MENOS ESTE NÚMERO DE EVENTOS GRANDES",
                              options=[1, 2, 3, 4], index=1)
ind = INDICADORES[ind_nombre]

df_f = df[(df.anio.isin(filtro_anio)) & (df.temporada.isin(filtro_temporada)) & (df.periodo.isin(filtro_periodo))]

if df_f.shape[0] == 0:
    st.warning("No hay meses con los filtros escogidos. Realice un cambio en los filtros (año, temporada o periodo) para ver los resultados.")
    st.stop()

# Indicadores principales 
st.subheader("Indicadores principales (promedio mensual)")
a, b, c, d, e = st.columns(5)
a.metric(label="OCUPACIÓN HOTELERA", value=f"{df_f.ocupacion_ema_antioquia.mean():.1f}%", border=True)
b.metric(label="ÍNDICE DE TARIFA", value=f"{df_f.indice_tarifa_ema_antioquia.mean():.1f}", border=True)
c.metric(label="EXTRANJEROS", value=f"{df_f.entradas_extranjeros_jmc.mean():,.0f}", border=True)
d.metric(label="TRÁFICO", value=f"{df_f.trafico_total.mean():,.0f}", border=True)
e.metric(label="EVENTOS GRANDES", value=f"{df_f.n_eventos_grandes.mean():.1f}", border=True)

st.divider()

# Serie de tiempo con eventos marcados
st.subheader("Serie de tiempo con los meses de eventos marcados")
fig = px.line(data_frame=df_f, x="fecha", y=ind)
df_ev = df_f[df_f.n_eventos_grandes >= umbral]
fig_ev = px.scatter(data_frame=df_ev, x="fecha", y=ind,
                    hover_data=["n_eventos_grandes", "n_conciertos", "n_festivales"])
fig_ev.update_traces(marker=dict(size=10, color="crimson"))
fig.add_traces(fig_ev.data)
fig.add_vrect(x0="2020-03-01", x1="2021-12-31", fillcolor="grey", opacity=0.15,
              line_width=0, annotation_text="COVID")
fig.update_layout(xaxis_title="Fecha", yaxis_title=ind_nombre, showlegend=False)
st.plotly_chart(fig, width="stretch")
st.caption(f"Los puntos rojos son los meses con al menos {umbral} eventos grandes. La zona gris es el periodo COVID.")

st.divider()

# Con vs sin evento grande 
st.subheader("Meses con y sin evento grande")
df_comp = df_f.groupby("evento", as_index=False)[ind].mean()

izq, der = st.columns(2)
fig = px.bar(data_frame=df_comp, x="evento", y=ind, color="evento", text_auto=".1f")
fig.update_layout(xaxis_title="", yaxis_title=ind_nombre, showlegend=False)
izq.plotly_chart(fig, width="stretch")

tabla = (df_f.groupby("evento", as_index=False)
         .agg(meses=("mes", "count"),
              ocupacion=("ocupacion_ema_antioquia", "mean"),
              tarifa=("indice_tarifa_ema_antioquia", "mean"),
              extranjeros=("entradas_extranjeros_jmc", "mean"),
              trafico=("trafico_total", "mean")).round(1))
der.dataframe(tabla, hide_index=True, width="stretch")

if df_comp.shape[0] == 2:
    con = df_comp.loc[df_comp.evento == "Con evento grande", ind].iloc[0]
    sin = df_comp.loc[df_comp.evento == "Sin evento grande", ind].iloc[0]
    st.info(f"Con los filtros actuales, en los meses con evento grande el indicador **{ind_nombre}** cambia {(con / sin - 1) * 100:+.1f}% frente a los meses sin evento grande.")
else:
    st.info("Con los filtros actuales solo hay un grupo (con o sin evento grande), así que no se puede comparar.")

st.markdown("La temporada alta (enero, junio, julio, agosto y diciembre) y el COVID también mueven el turismo. Por eso conviene usar los filtros de temporada y periodo para separar su efecto del de los eventos.")

st.divider()

#  Correlaciones
st.subheader("Correlación de los eventos grandes con el turismo")
df_corr = pd.DataFrame({
    "indicador": list(INDICADORES),
    "correlacion": [df_f["n_eventos_grandes"].corr(df_f[x]) for x in INDICADORES.values()]})
fig = px.bar(data_frame=df_corr, x="correlacion", y="indicador", orientation="h", text_auto=".2f")
fig.update_layout(xaxis_title="Correlación con el número de eventos grandes", yaxis_title="",
                  showlegend=False, xaxis_range=[-1, 1])
st.plotly_chart(fig, width="stretch")
st.caption("Correlación no implica causalidad.")

st.divider()



# Limitaciones 
st.subheader("Limitaciones de los datos")
st.markdown("""
- Ocupación y tarifa son de **Antioquia**, no solo de Medellín.
- La tarifa es un **índice (base 2019=100)**, no pesos.
- Las entradas son de **extranjeros** por el aeropuerto José María Córdova (no todos son turistas).
- El tráfico es de solo 2 peajes (Las Palmas y Guarne) e incluye todo tipo de vehículos.
- La base de eventos es un **mínimo verificado**; solo 29 de 89 eventos tienen aforo, así que `aforo_total` es indicativo.
- Los datos son mensuales: un concierto de 2 o 3 días se diluye en el mes.
- 79 de 89 eventos son "grandes", por eso el criterio de evento grande separa poco.
- Las variaciones de 2020 y 2021 están distorsionadas por el COVID.
""")