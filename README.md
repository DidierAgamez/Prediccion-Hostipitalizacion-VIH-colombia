# Predicción de la hospitalización en la notificación de VIH (SIVIGILA, Colombia, 2018–2025)

Entrega final del curso Machine Learning 2026-II, Universidad Tecnológica de Bolívar.

Autores: Didier Agamez, Angel Vega, Germán de Armas y Karla Barraza.

El artículo se genera completo desde un único archivo Quarto (`articulo_ML_Agamez_final.qmd`). Todas las cifras, tablas y figuras salen del código; ninguna está escrita a mano.

## Contenido

| Archivo | Qué es |
|---|---|
| `articulo_ML_Agamez_final.qmd` | Fuente del artículo: texto, análisis, modelos, tablas y figuras |
| `articulo_ML_Agamez_final.pdf` | Artículo generado con la base completa |
| `BD_2008_2025_unido_850.csv.gz` | Microdatos del evento 850 (VIH/SIDA/mortalidad por SIDA) del SIVIGILA, archivos anuales unidos |
| `referencias.bib`, `apa.csl` | Bibliografía y estilo APA |
| `modelo_hospitalizacion_vih.joblib` | Modelo definitivo con su contrato (Pipeline completo, umbral, columnas, versiones). Lo genera el `.qmd` |
| `resultados/cv_resultados.csv` | Resultados por pliegue de la validación cruzada. Lo genera el `.qmd` |
| `cargar_y_predecir.py` | Carga el modelo guardado y predice una notificación de ejemplo |
| `app.py` | Servicio web (Flask) que expone el modelo |
| `requirements.txt` | Versiones exactas de los paquetes con que se generó el PDF |

## Requisitos

- Python 3.12
- [Quarto](https://quarto.org) 1.10 o posterior, con una instalación de LaTeX que tenga `xelatex`. Si no tiene LaTeX, instale TinyTeX con `quarto install tinytex`.

## Instalación

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux o macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## Reproducir el artículo

Desde esta carpeta y con el entorno activado:

```bash
quarto render articulo_ML_Agamez_final.qmd --to pdf
```

- Con la base completa, el render tarda alrededor de 75 minutos (la validación cruzada anidada es la parte más lenta).
- Para un ensayo rápido, cambie `MUESTRA_DESARROLLO = None` por `MUESTRA_DESARROLLO = 12_000` en el bloque de configuración del `.qmd`. Tarda unos 13 minutos. Las cifras de ese ensayo no son las del artículo, así que vuelva a dejar `None` antes del render definitivo.
- El render sobrescribe `modelo_hospitalizacion_vih.joblib` y `resultados/cv_resultados.csv`.
- Los resultados se reproducen con la semilla fijada en el `.qmd`.

Si Quarto no encuentra el Python del entorno (en Windows puede aparecer `os error 1920` por el alias de la Microsoft Store), indíquelo de forma explícita:

```powershell
# PowerShell
$env:QUARTO_PYTHON = "$PWD\.venv\Scripts\python.exe"
```

```bash
# Linux o macOS
export QUARTO_PYTHON="$PWD/.venv/bin/python"
```

## Usar el modelo

Ambos scripts leen `modelo_hospitalizacion_vih.joblib` con una ruta relativa, así que deben ejecutarse desde esta carpeta.

Predicción de una fila de ejemplo:

```bash
python cargar_y_predecir.py
```

Servicio web en `http://127.0.0.1:5000`:

```bash
python app.py
```

- `GET /health` devuelve el estado, la versión del modelo, el umbral y las columnas del contrato.
- `POST /predict` recibe un objeto JSON o una lista de objetos con las columnas del contrato (`null` = dato faltante) y devuelve la probabilidad y la decisión según el umbral.

Ejemplo:

```bash
curl -X POST http://127.0.0.1:5000/predict -H "Content-Type: application/json" -d '{"edad": 41, "anio": 7, "estrato_n": 2, "dias_sintomas": null, "gestante": 0, "migrante": 0, "privado_libertad": 0, "desplazado": 0, "discapacidad": 0, "habitante_calle": 0, "victima_violencia": 0, "centro_psiquiatrico": 0, "sexo": "M", "regimen": "Subsidiado", "area": "Cabecera", "etnia": "Otro", "region": "Caribe"}'
```

Si las versiones instaladas de numpy, pandas, scikit-learn o xgboost no coinciden con las del modelo guardado, los scripts muestran un aviso. Instale las de `requirements.txt`.

## Datos

Los microdatos son públicos. Se descargaron del [portal del SIVIGILA](https://portalsivigila.ins.gov.co/Paginas/Buscador.aspx) del Instituto Nacional de Salud de Colombia. La fecha de descarga y la descripción de las variables están en el artículo.
