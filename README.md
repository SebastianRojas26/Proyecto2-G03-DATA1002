# Turismo y conciertos/festivales en Medellín (DATA-1002, Proyecto 2)

**Pregunta analítica:** ¿Cómo se relacionan los grandes conciertos y festivales con la actividad turística de Medellín (ocupación hotelera, tarifas, llegadas internacionales, tráfico)?


## Estructura
```
data/raw/        bases originales de datos.gov.co, sin modificar, y eventos_medellin.csv (base propia, Rol 3)
data/processed/  bases limpias, panel_publico.csv (Rol 1) y panel_final.csv (panel + eventos, Rol 3)
notebooks/       01_limpieza_y_union.ipynb (Rol 1), 02_Union_bases.ipynb (Rol 3) y análisis exploratorio (Rol 2)
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
# luego, correr notebooks/02_Union_bases.ipynb (desde la carpeta notebooks/):
# une panel_publico.csv con data/raw/eventos_medellin.csv y genera data/processed/panel_final.csv
```

## Fuentes (datos abiertos; licencia: por confirmar en la ficha de cada fuente)
| Base | ID | Periodo en el archivo | Limitaciones |
|---|---|---|---|
| Tráfico vehicular ANI | 8yi9-t44c | 2014-01 a 2026-05 (todo el país) | Solo se usan 2 peajes. Incluye todo tipo de vehículos (no solo turistas). |
| DANE – Encuesta Mensual de Alojamiento (EMA), anexos sep-2026 | (Excel, [página EMA](https://www.dane.gov.co/index.php/estadisticas-por-tema/servicios/encuesta-mensual-de-alojamiento-ema); [ficha metodológica](https://www.dane.gov.co/files/operaciones/EMA/fmet-EMA.pdf)) | 2019-01 a 2026-09 (cifras desde 2023 son provisionales) | Región **Antioquia, no solo Medellín**. La tarifa es un **índice (base 2019=100), no pesos**; el anexo solo lo da por tipo de acomodación (sencilla y doble), y el panel usa también su promedio simple. |
| Migración Colombia – Entradas de extranjeros a Colombia | 96sh-4v8d | 2012-01 a 2026-06 (país completo) | El archivo no trae el nombre del puesto migratorio, solo sus coordenadas: se filtró el Aeropuerto José María Córdova (Rionegro) por coordenadas. Suma todas las nacionalidades. Es entrada de extranjeros, no turistas (incluye otros motivos de viaje). |
| **Base propia de eventos en Medellín** (Rol 3) | `data/raw/eventos_medellin.csv` | 2019-01 a 2026-01 (89 eventos; el último, Alumbrados 2025, termina en enero de 2026) | Es un mínimo verificado, no un censo: solo entran eventos con prensa o fuente oficial que confirme que se hicieron. Solo 29 de 89 tienen aforo. |

## Limpieza y unión (`src/limpiar_y_unir.py`; versión en notebook: `notebooks/01_limpieza_y_union.ipynb`)
- Fechas a año-mes (`YYYY-MM`) en todas las bases.
- Duplicados: en ANI se eliminan filas repetidas por peaje, categoría y mes (había 0).
- **Peajes ANI elegidos: LAS PALMAS y GUARNE.** Se eligieron por estar en la ruta Medellín – Oriente antioqueño / aeropuerto José María Córdova (criterio propio del equipo, por confirmar); tienen serie completa (149 meses, 2014-01 a 2026-05) y sin duplicados. Se suma el tráfico de todas las categorías (`trafico_total`) y se guarda aparte la categoría I, vehículos livianos (`trafico_livianos`).
- EMA: se toma la región Antioquia. Los años desde 2023 vienen como "2023p" (provisional): se extrae el año. El índice de tarifa se da por acomodación sencilla y doble, y se calcula su promedio simple.
- Migración: se filtra el Aeropuerto José María Córdova por coordenadas y se suman todas las nacionalidades por mes.
- El panel se limita a **2019-01 a 2025-12** (84 meses), periodo pedido por el equipo.
- Salida: `data/processed/panel_publico.csv` (84 meses x 12 columnas, sin faltantes). Verificación de la unión en `data/processed/verificacion_union.txt`.

## Base propia de eventos (Rol 3, `data/raw/eventos_medellin.csv`)
Grandes conciertos, festivales, ferias y temporadas en Medellín entre 2019 y 2025: 89 eventos (2019: 17, 2020: 2, 2021: 6, 2022: 21, 2023: 14, 2024: 14, 2025: 15).

**Cómo se construyó**
1. **Candidatos:** búsquedas por año en setlist.fm para Medellín, más las ferias y temporadas de la ciudad (Feria de las Flores, Alumbrados, Colombiatex, Colombiamoda, Altavoz).
2. **Escala:** solo escenarios grandes (Estadio Atanasio Girardot, La Macarena, Estadio Cincuentenario, Parque Norte, Plaza Mayor, Aeroparque Juan Pablo II) o espacio público en eventos de ciudad.
3. **Regla de inclusión:** un evento entra solo si hay una nota de prensa del mismo día o posterior, o un balance oficial (p. ej., Alcaldía de Medellín), que confirme que se hizo. Un anuncio previo más setlist.fm no alcanza: hubo eventos anunciados que se cancelaron (Young Miko 2024, Bad Bunny 2019, el primer día de Afterlife 2024 por lluvia).
4. **Escenario:** siempre el que reporta la prensa.
5. Se excluyen eventos virtuales (2020–2021), los de fuera de Medellín (Rionegro, Copacabana) y los que no tenían prensa posterior.

**Columnas**

| Columna | Descripción |
|---|---|
| `fecha_inicio`, `fecha_fin` | Primer y último día (AAAA-MM-DD). |
| `nombre` | Evento o gira; si tuvo varias fechas se indica entre paréntesis. |
| `tipo` | `concierto`, `concierto_gratuito`, `festival`, `feria`, `feria_comercial` o `temporada`. |
| `artista_principal` | Artistas destacados separados por `;` (vacío en ferias y temporadas). |
| `escenario` | Escenario exacto en Medellín. |
| `aforo_estimado` | Asistencia reportada; vacío si no hay cifra confiable. En la Feria de las Flores se deja vacío a propósito. |
| `internacional` | `si` si el artista principal o el cartel es internacional. |
| `fuente_url`, `evidencia` | Enlace que confirma el evento y tipo de evidencia. |

**Criterio de "evento grande":** cumple al menos una condición: aforo ≥ 20.000, internacional, tipo `festival`/`feria`/`feria_comercial`/`temporada`, o escenario Estadio Atanasio Girardot. 79 de los 89 eventos son grandes.

## Unión con los eventos (Rol 3, `notebooks/02_Union_bases.ipynb`)
1. Se carga `panel_publico.csv` y `eventos_medellin.csv`; las fechas se pasan a `datetime` (eventos de un día: `fecha_fin` = `fecha_inicio`).
2. Cada evento se pasa a los meses que dura (`period_range` + `explode`): por ejemplo, los Alumbrados de diciembre a enero cuentan en los dos meses.
3. Se agrega por mes (`groupby` + `agg`) y se une al panel por la columna `mes` con `merge(how="left", validate="one_to_one")`. Los meses sin eventos quedan en 0.
4. Se agregan variables de control: `covid` y `temporada_alta`.
5. Verificación: 84 filas x 21 columnas, 0 meses duplicados, 0 faltantes. Solo queda por fuera 2026-01 (Alumbrados 2025), que está fuera del periodo.

**Salida: `data/processed/panel_final.csv`**: las 12 columnas de `panel_publico.csv` más:

| Columna | Descripción |
|---|---|
| `n_eventos` | Eventos activos en el mes. |
| `n_eventos_grandes` | Eventos grandes en el mes. |
| `n_conciertos`, `n_festivales`, `n_internacionales` | Conteos por tipo (`n_festivales` incluye ferias y temporadas). |
| `aforo_total` | Suma de aforos conocidos; solo indicativa. |
| `hay_evento_grande` | 1 si hubo al menos un evento grande en el mes. |
| `covid` | 1 entre 2020-03 y 2021-12. |
| `temporada_alta` | 1 en enero, junio, julio, agosto y diciembre. |

**Limitaciones de los eventos**
- Es un mínimo verificado: `n_eventos` subestima la actividad real.
- Los datos turísticos son mensuales y de Antioquia; un concierto de 2–3 días se diluye en el mes.
- Urban Music Awards 2019 y Rels B 2022 se confirmaron por el equipo y no por prensa posterior.

## Licencias y atribución
- **DANE (EMA):** los términos de uso del DANE autorizan usar, transformar y analizar la información citando la fuente. Fuente: Departamento Administrativo Nacional de Estadística: www.dane.gov.co (https://www.dane.gov.co/index.php/terrminos-y-condiciones-dane).
- **Tráfico vehicular ANI:** publicado por la Agencia Nacional de Infraestructura (ANI) en datos.gov.co, actualizado el 2 de septiembre de 2026. En la ficha el campo "Licencia" aparece vacío; solo trae el enlace de la fuente (https://www.ani.gov.co).
- **Entradas de extranjeros a Colombia:** publicado por la Unidad Administrativa Especial Migración Colombia en datos.gov.co, actualizado el 20 de agosto de 2026 (frecuencia semestral). En la ficha el campo "Licencia" aparece vacío; solo trae el enlace de la fuente.
- **Base propia de eventos:** elaborada por el equipo a partir de notas de prensa y de la Alcaldía de Medellín; cada fila trae el enlace a su fuente en `fuente_url`.
- Los datasets de datos.gov.co se usan como datos abiertos del Portal Nacional de Datos Abiertos, citando a la entidad publicadora. Fichas consultadas el 22 de noviembre de 2026.
