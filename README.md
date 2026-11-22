# Turismo y conciertos/festivales en Medellín (DATA-1002, Proyecto 2)

**Pregunta analítica:** ¿Cómo se relacionan los grandes conciertos y festivales con la actividad turística de Medellín (ocupación hotelera, tarifas, llegadas internacionales, tráfico)?

> Nota: el componente de arriendos se descartó por acuerdo del equipo, porque no hay datos públicos mensuales y específicos de arriendos para Medellín (la base "Arrendamiento histórico" de datos.gov.co es un listado de inmuebles del Municipio, sin fechas ni canon).

## Estructura
```
data/raw/        bases originales de datos.gov.co, sin modificar
data/processed/  bases limpias y panel_publico.csv
notebooks/       01_limpieza_y_union.ipynb (Rol 1) y análisis exploratorio (Rol 2)
src/             código de descarga, limpieza y unión
dashboard/       dashboard (Rol 2)
```

## Cómo correr el proyecto
```
pip install -r requirements.txt
python src/descargar_datos.py     # baja ANI y Migración (datos.gov.co) a data/raw
# además, poner a mano en data/raw: ema_anexos_sep2026.xlsx (DANE, ver enlace en src/descargar_datos.py)
python src/limpiar_y_unir.py      # limpia y genera data/processed/panel_publico.csv
# el mismo proceso, paso a paso, está en notebooks/01_limpieza_y_union.ipynb
```

## Fuentes (datos abiertos; licencia: por confirmar en la ficha de cada fuente)
| Base | ID | Periodo en el archivo | Limitaciones |
|---|---|---|---|
| Tráfico vehicular ANI | 8yi9-t44c | 2014-01 a 2026-05 (todo el país) | Solo se usan 2 peajes. Incluye todo tipo de vehículos (no solo turistas). |
| DANE – Encuesta Mensual de Alojamiento (EMA), anexos sep-2026 | (Excel, [página EMA](https://www.dane.gov.co/index.php/estadisticas-por-tema/servicios/encuesta-mensual-de-alojamiento-ema); [ficha metodológica](https://www.dane.gov.co/files/operaciones/EMA/fmet-EMA.pdf)) | 2019-01 a 2026-09 (cifras desde 2023 son provisionales) | Región **Antioquia, no solo Medellín**. La tarifa es un **índice (base 2019=100), no pesos**; el anexo solo lo da por tipo de acomodación (sencilla y doble), y el panel usa también su promedio simple. |
| Migración Colombia – Entradas de extranjeros a Colombia | 96sh-4v8d | 2012-01 a 2026-06 (país completo) | El archivo no trae el nombre del puesto migratorio, solo sus coordenadas: se filtró el Aeropuerto José María Córdova (Rionegro) por coordenadas. Suma todas las nacionalidades. Es entrada de extranjeros, no turistas (incluye otros motivos de viaje). |

## Limpieza y unión (`src/limpiar_y_unir.py`; versión en notebook: `notebooks/01_limpieza_y_union.ipynb`)
- Fechas a año-mes (`YYYY-MM`) en todas las bases.
- Duplicados: en ANI se eliminan filas repetidas por peaje, categoría y mes (había 0).
- **Peajes ANI elegidos: LAS PALMAS y GUARNE.** Se eligieron por estar en la ruta Medellín – Oriente antioqueño / aeropuerto José María Córdova (criterio propio del equipo, por confirmar); tienen serie completa (149 meses, 2014-01 a 2026-05) y sin duplicados. Se suma el tráfico de todas las categorías (`trafico_total`) y se guarda aparte la categoría I, vehículos livianos (`trafico_livianos`).
- EMA: se toma la región Antioquia. Los años desde 2023 vienen como "2023p" (provisional): se extrae el año. El índice de tarifa se da por acomodación sencilla y doble, y se calcula su promedio simple.
- Migración: se filtra el Aeropuerto José María Córdova por coordenadas y se suman todas las nacionalidades por mes.
- El panel se limita a **2019-01 a 2025-12** (84 meses), periodo pedido por el equipo.
- Salida: `data/processed/panel_publico.csv` (84 meses x 12 columnas, sin faltantes). Verificación de la unión en `data/processed/verificacion_union.txt`.

## Licencias y atribución
- **DANE (EMA):** los términos de uso del DANE autorizan usar, transformar y analizar la información citando la fuente. Fuente: Departamento Administrativo Nacional de Estadística: www.dane.gov.co (https://www.dane.gov.co/index.php/terrminos-y-condiciones-dane).
- **Tráfico vehicular ANI:** publicado por la Agencia Nacional de Infraestructura (ANI) en datos.gov.co, actualizado el 2 de septiembre de 2026. En la ficha el campo "Licencia" aparece vacío; solo trae el enlace de la fuente (https://www.ani.gov.co).
- **Entradas de extranjeros a Colombia:** publicado por la Unidad Administrativa Especial Migración Colombia en datos.gov.co, actualizado el 20 de agosto de 2026 (frecuencia semestral). En la ficha el campo "Licencia" aparece vacío; solo trae el enlace de la fuente.
- Los datasets de datos.gov.co se usan como datos abiertos del Portal Nacional de Datos Abiertos, citando a la entidad publicadora. Fichas consultadas el 22 de noviembre de 2026.
