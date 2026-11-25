# Tablero del artículo

Interfaz para mostrar los resultados y clasificar fichas de prueba. Es lo único que hay que desplegar: carga el
modelo ya entrenado y predice con `cargar_y_predecir.py`. No entrena nada y no modifica los archivos del artículo.

## Correrlo en el computador

Desde la raíz del repositorio, con el entorno activado:

```powershell
uv pip install streamlit          # una sola vez
streamlit run dashboard/dashboard.py
```

Se abre en http://localhost:8501.

## Qué lee

| Archivo (en la raíz) | Para qué |
|---|---|
| `modelo_hospitalizacion_vih.joblib` | Modelo, umbral, métricas de prueba, categorías y caducidad |
| `cargar_y_predecir.py` | Funciones `cargar()` y `predecir()` |
| `resultados/cv_resultados.csv` | Gráfica por pliegue |
| `dashboard/datos/fichas_sinteticas.json` | Ocho fichas inventadas; se pueden editar o agregar más |

Las cifras salen de esos archivos. Si el artículo se vuelve a generar, el tablero se actualiza al recargar la página.
Un render de ensayo (`MUESTRA_DESARROLLO = 12_000`) sobrescribe el modelo y el CSV: antes de presentar, verifique
que el tablero muestre el umbral y el AUC del artículo final.

## Publicarlo en la web (opcional)

En Streamlit Community Cloud: elegir el repositorio, archivo principal `dashboard/dashboard.py`. La plataforma
instala `dashboard/requirements.txt` (no necesita torch ni Quarto). El repositorio debe incluir el `.joblib`,
`cargar_y_predecir.py` y `resultados/cv_resultados.csv`.

## Y `app.py`

`app.py` expone la misma función `predecir()` como servicio web (`/health`, `/predict`) para que otros sistemas
consulten el modelo. El tablero no lo usa.
