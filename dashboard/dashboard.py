"""Tablero del artículo
«Predicción de la hospitalización en la notificación de VIH con datos de vigilancia: SIVIGILA, Colombia, 2018–2025».

Uso, desde la raíz del repositorio y con el entorno activado:
    streamlit run dashboard/dashboard.py

Es lo único que hay que desplegar. No entrena nada: reutiliza lo que genera el artículo.
    modelo_hospitalizacion_vih.joblib   modelo y contrato
    cargar_y_predecir.py                funciones cargar() y predecir() (la predicción vive ahí)
    resultados/cv_resultados.csv        resultados por pliegue
Las cifras de desempeño se leen de esos archivos; si el artículo se vuelve a generar, el tablero cambia solo.
app.py (Flask) expone la misma función predecir() como servicio para otros sistemas; el tablero no lo necesita.
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------------------------------------------------------
# Configuración
# ----------------------------------------------------------------------------------------------------------------------
AQUI = Path(__file__).resolve().parent
# Raíz del repositorio (donde están el .joblib y cargar_y_predecir.py). Se puede cambiar con CARPETA_ARTICULO.
CARPETA = Path(os.environ.get("CARPETA_ARTICULO", AQUI.parent)).resolve()

# Contexto tomado del artículo (no son métricas del modelo; esas se leen del contrato)
SOBRETITULO = "SIVIGILA · VIH · Colombia, 2018–2025"
TITULO = "¿Quién llegó hospitalizado al diagnóstico?"
SUBTITULO = ("Predicción de la hospitalización en la notificación de VIH con datos de vigilancia, "
             "para decidir a quién contacta primero la secretaría de salud.")
AUTORES = ["Didier Agamez", "Angel Vega", "Germán de Armas", "Karla Barraza"]
CASOS_UTILES = 142_379
ANIO_FIN = 2025                 # último año con el que se entrenó
DIAS_MAX = 3650                 # intervalos mayores se tratan como dato faltante, igual que en el artículo
C_FP, C_FN = 300_000, 1_500_000  # costos con los que se eligió el umbral

# Paleta (crema, tinta y un acento; la misma línea visual de los otros proyectos del grupo)
FONDO, TARJETA, TINTA, TENUE, LINEA = "#FEFAF3", "#FFFFFF", "#190F0A", "#695B50", "#E5DCD4"
ACENTO, ACENTO_TINTA, VERDE, NEUTRO = "#F3821D", "#B4550A", "#007A64", "#B9AA9C"
AMBAR, GRIS = ACENTO_TINTA, TENUE      # prioritaria / texto secundario

ETIQ_GRUPOS = {
    "gestante": "Gestante", "migrante": "Migrante", "privado_libertad": "Privado de la libertad",
    "desplazado": "Desplazado", "discapacidad": "Con discapacidad", "habitante_calle": "Habitante de calle",
    "victima_violencia": "Víctima de violencia", "centro_psiquiatrico": "En centro psiquiátrico",
}
ETIQ_SEXO = {"F": "Mujer", "M": "Hombre"}

st.set_page_config(page_title="VIH · SIVIGILA · Tablero", page_icon="🩺", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap');
html, body, .stMarkdown p, .stMarkdown li, label, button p, input {{font-family: "Inter", system-ui, "Segoe UI", sans-serif;}}
.stApp {{background: radial-gradient(900px 420px at 100% -5%, #FBE3C8 0%, transparent 60%), {FONDO};}}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stToolbar"] {{display: none;}}
.block-container {{padding-top: 2.4rem; max-width: 1280px;}}
h1, h2, h3, h1 span, h2 span, h3 span {{font-family: "Fraunces", Georgia, "Times New Roman", serif !important; color: {TINTA};
            letter-spacing: -.015em; font-weight: 600 !important;}}
.cabecera {{display: flex; justify-content: space-between; align-items: flex-end; gap: 2rem; margin-bottom: 1.1rem;}}
.sobre {{font-size: .75rem; letter-spacing: .17em; text-transform: uppercase; color: {ACENTO_TINTA}; font-weight: 600;}}
.cabecera h1 {{font-size: clamp(2rem, 3.6vw, 3.1rem); line-height: 1.05; margin: .35rem 0 .5rem 0; padding: 0;}}
.cabecera h1 em {{font-style: italic; color: {ACENTO_TINTA};}}
.cabecera .sub {{font-size: 1.05rem; color: {TENUE}; max-width: 46rem;}}
.sello {{background: {TARJETA}; border: 1px solid {LINEA}; border-radius: 16px; padding: .8rem 1.1rem; min-width: 215px;
        box-shadow: 0 1px 2px #1e130e0f, 0 8px 24px -8px #1e130e1f; font-size: .85rem; color: {TENUE}; line-height: 1.5;}}
.sello strong {{display: block; font-size: 1.05rem; color: {TINTA};}}
.rot {{font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; color: {TENUE}; font-weight: 600;}}
.tarjeta {{background: {TARJETA}; border: 1px solid {LINEA}; border-radius: 16px; padding: 1rem 1.2rem; height: 100%;
          border-top: 4px solid var(--c, {LINEA}); box-shadow: 0 1px 2px #1e130e0f, 0 8px 24px -8px #1e130e1f;}}
.tarjeta .val {{font-family: "Fraunces", Georgia, serif; font-size: 2.2rem; font-weight: 600; color: {TINTA};
               line-height: 1.15; margin-top: .2rem;}}
.tarjeta .nota {{font-size: .86rem; color: {TENUE}; margin-top: .2rem;}}
.aviso {{background: #FFF3E3; border: 1px solid #F3D3AE; border-radius: 12px; padding: .6rem 1rem; font-size: .9rem;
        color: #5B3A1A; margin-bottom: 1rem;}}
.lead {{font-size: 1.12rem; color: {TENUE}; max-width: 54rem; margin: -.4rem 0 1rem 0;}}
.resultado {{background: {TARJETA}; border: 1px solid {LINEA}; border-radius: 18px; padding: 1.4rem 1.6rem;
            box-shadow: 0 2px 4px #1e130e14, 0 20px 40px -12px #1e130e2e;}}
.resultado .prob {{font-family: "Fraunces", Georgia, serif; font-size: 3.8rem; font-weight: 700; line-height: 1;
                  margin-top: .3rem;}}
.pastilla {{display: inline-block; padding: .4rem 1rem; border-radius: 999px; font-weight: 700; font-size: .92rem;
           letter-spacing: .04em; color: #fff; margin-top: .7rem;}}
.barra {{position: relative; height: 16px; border-radius: 8px; background: #EFE6DB; margin: 1.6rem 0 1.9rem 0;}}
.barra .lleno {{height: 100%; border-radius: 8px;}}
.barra .umbral {{position: absolute; top: -7px; width: 3px; height: 30px; background: {TINTA};}}
.barra .umbral span {{position: absolute; top: 32px; left: -60px; width: 120px; text-align: center; font-size: .76rem;
                     color: {TINTA}; white-space: nowrap;}}
.pasos li {{margin-bottom: .3rem;}}
.equipo {{display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .4rem;}}
.equipo span {{background: {TARJETA}; border: 1px solid {LINEA}; border-radius: 999px; padding: .3rem .9rem;
              font-size: .9rem;}}
.pie {{color: {TENUE}; font-size: .8rem; margin-top: 2.2rem; text-align: center;}}
div[data-testid="stTabs"] button p {{font-size: 1rem; font-weight: 600;}}
div[data-testid="stTabs"] [data-baseweb="tab-list"] {{gap: 1.4rem;}}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------------------------------------------------
# Carga de lo que ya existe
# ----------------------------------------------------------------------------------------------------------------------
if not (CARPETA / "cargar_y_predecir.py").exists():
    st.error(f"No encuentro la carpeta del artículo en:\n\n`{CARPETA}`\n\n"
             "Ajuste la variable de entorno CARPETA_ARTICULO o la constante CARPETA de dashboard.py.")
    st.stop()
sys.path.insert(0, str(CARPETA))
import cargar_y_predecir as cyp  # noqa: E402  (funciones del artículo, sin modificar)


@st.cache_resource(show_spinner="Cargando el modelo guardado…")
def contrato_local(mtime):
    return cyp.cargar(str(CARPETA / cyp.ARCHIVO_MODELO))


@st.cache_data
def resultados_cv(mtime):
    return pd.read_csv(CARPETA / "resultados" / "cv_resultados.csv")


@st.cache_data
def fichas_sinteticas():
    return json.loads((AQUI / "datos" / "fichas_sinteticas.json").read_text(encoding="utf-8"))


def clasificar(filas):
    """La predicción vive en cargar_y_predecir.py: se llama a predecir() con el contrato cargado."""
    return cyp.predecir(CONTRATO, filas), "cargar_y_predecir.py · predecir()", CONTRATO["umbral"]


CONTRATO = contrato_local((CARPETA / cyp.ARCHIVO_MODELO).stat().st_mtime)
CV = resultados_cv((CARPETA / "resultados" / "cv_resultados.csv").stat().st_mtime)
UMBRAL = CONTRATO["umbral"]
MP = CONTRATO["metrica_prueba"]
PREV = CONTRATO["prevalencia_entrenamiento"]
CATS = CONTRATO["categorias"]
ANIO_INICIO = CONTRATO["anio_inicio"]


def pct(x, d=1):
    return f"{100 * x:.{d}f} %"


def miles(n):
    return f"{n:,.0f}".replace(",", " ")


def tarjeta(rotulo, valor, nota="", color=LINEA):
    st.markdown(f'<div class="tarjeta" style="--c:{color}"><div class="rot">{rotulo}</div><div class="val">{valor}</div>'
                f'<div class="nota">{nota}</div></div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------------------------------------------------------
# Encabezado
# ----------------------------------------------------------------------------------------------------------------------
st.markdown(f"""
<div class="cabecera">
  <div><span class="sobre">{SOBRETITULO}</span>
    <h1>{TITULO.replace("hospitalizado", "<em>hospitalizado</em>")}</h1>
    <div class="sub">{SUBTITULO}</div></div>
  <div class="sello"><span class="rot">Modelo cargado</span>
    <strong>{CONTRATO['modelo']} · v{CONTRATO['version_modelo']}</strong>
    Umbral {UMBRAL:.2f} · AUC {MP['AUC']:.3f}<br>Entrenado el {CONTRATO['entrenado_el']}</div>
</div>
<div class="aviso"><b>Demostración académica.</b> Las fichas que se clasifican aquí son inventadas. El sistema no
decide hospitalizar ni reemplaza el criterio clínico: ordena a quién contactar primero.</div>
""", unsafe_allow_html=True)

t_resumen, t_modelos, t_ficha, t_servicio = st.tabs(
    ["1 · Resumen", "2 · Comparación de modelos", "3 · Clasificar una ficha", "4 · Límites y despliegue"])

# ----------------------------------------------------------------------------------------------------------------------
# 1. Resumen
# ----------------------------------------------------------------------------------------------------------------------
with t_resumen:
    st.subheader("La pregunta")
    st.markdown("Con lo que trae la ficha de notificación, **¿qué tan probable es que la persona haya llegado "
                "hospitalizada al momento del diagnóstico?** La hospitalización al notificar es una señal de "
                "diagnóstico tardío. La secretaría de salud usa esa probabilidad para decidir a quién contactar el "
                "mismo día.")
    c = st.columns(4)
    with c[0]:
        tarjeta("Casos analizados", miles(CASOS_UTILES), f"notificaciones de VIH, {ANIO_INICIO}–{ANIO_FIN}", "#1D6FD6")
    with c[1]:
        tarjeta("Hospitalizados al notificar", pct(PREV), "prevalencia en el entrenamiento", "#F94144")
    with c[2]:
        tarjeta("AUC en prueba", f"{MP['AUC']:.3f}", f"en {miles(MP['casos'])} casos nunca vistos", "#45BA50")
    with c[3]:
        tarjeta("Umbral de decisión", f"{UMBRAL:.2f}", "elegido por costo, no por exactitud", ACENTO)

    st.write("")
    izq, der = st.columns([1.15, 1])
    with izq:
        st.subheader("Qué logra la regla en la prueba")
        detecta = round(100 * MP["sensibilidad"])
        puntos = pd.DataFrame({"i": range(100)})
        puntos["col"], puntos["fila"] = puntos.i % 20, puntos.i // 20
        puntos["estado"] = ["Detectado" if i < detecta else "No detectado" for i in puntos.i]
        st.altair_chart(
            alt.Chart(puntos).mark_circle(size=230, opacity=1).encode(
                x=alt.X("col:O", axis=None), y=alt.Y("fila:O", axis=None),
                color=alt.Color("estado:N", scale=alt.Scale(domain=["Detectado", "No detectado"],
                                                            range=[ACENTO, "#E9DED2"]),
                                legend=alt.Legend(title=None, orient="bottom")),
                tooltip=["estado"]).properties(height=190).configure_view(stroke=None),
            width="stretch")
        st.markdown(f"De cada 100 personas que sí llegaron hospitalizadas, la regla marca **{detecta}** como "
                    f"prioritarias. De cada 100 marcadas, **{round(100 * MP['precision'])}** estaban "
                    f"hospitalizadas; el resto son contactos que no hacían falta.")
    with der:
        st.subheader("Por qué el umbral es bajo")
        st.markdown(f"""
- No encontrar a un hospitalizado (falso negativo) se valoró en **{miles(C_FN)} pesos**.
- Contactar a alguien sin necesidad (falso positivo), en **{miles(C_FP)} pesos**.
- Con esos costos el umbral teórico es {C_FP / (C_FP + C_FN):.3f}; el que minimiza el costo en los datos es **{UMBRAL:.2f}**.
- Por eso se prefiere marcar de más: sensibilidad **{pct(MP['sensibilidad'])}**, especificidad **{pct(MP['especificidad'])}**.
""")

# ----------------------------------------------------------------------------------------------------------------------
# 2. Comparación de modelos
# ----------------------------------------------------------------------------------------------------------------------
with t_modelos:
    st.subheader("Siete clasificadores, las mismas reglas")
    st.markdown('<p class="lead">Todos se midieron en los mismos cinco pliegues, así que la comparación es pareada: '
                'pliegue contra pliegue.</p>', unsafe_allow_html=True)
    with st.popover("Cómo leer esta gráfica"):
        st.markdown("- Cada **punto** es el resultado de un modelo en un pliegue de la validación cruzada anidada.\n"
                    "- El **rombo** es la media de los cinco pliegues y la línea va del peor al mejor.\n"
                    "- Más a la derecha es mejor. Si las líneas de dos modelos se cruzan mucho, la diferencia "
                    "puede ser ruido.\n"
                    "- En naranja, el modelo que quedó guardado.")
    clasif = CV[CV.metrica.isin(["AUC", "AP"])]
    nombres = {"AUC": "AUC (qué tan bien ordena)", "AP": "Precisión media (curva precisión-recall)"}
    metrica = st.radio("Métrica", list(nombres), format_func=nombres.get, horizontal=True)
    d = clasif[clasif.metrica == metrica]
    res = (d.groupby("modelo").valor.agg(media="mean", de="std", minimo="min", maximo="max")
           .sort_values("media", ascending=False).reset_index())
    orden = res.modelo.tolist()
    elegido = CONTRATO["modelo"]
    d = d.assign(grupo=d.modelo.map(lambda m: "Modelo elegido" if m == elegido else "Otros"))
    res_g = res.assign(grupo=res.modelo.map(lambda m: "Modelo elegido" if m == elegido else "Otros"))
    color = alt.Color("grupo:N", scale=alt.Scale(domain=["Modelo elegido", "Otros"], range=[ACENTO, NEUTRO]),
                      legend=alt.Legend(title=None, orient="top"))
    eje_y = alt.Y("modelo:N", sort=orden, title=None, axis=alt.Axis(labelFontSize=14, labelLimit=220))
    eje_x = alt.X("valor:Q", title=metrica, scale=alt.Scale(zero=False, padding=20),
                  axis=alt.Axis(format=".3f", labelFontSize=12, titleFontSize=13))
    rango = alt.Chart(res_g).mark_rule(strokeWidth=3, opacity=.35).encode(
        y=eje_y, x=alt.X("minimo:Q", title=metrica, scale=alt.Scale(zero=False, padding=20)), x2="maximo:Q",
        color=color)
    pts = alt.Chart(d).mark_circle(size=120, opacity=.7).encode(
        y=eje_y, x=eje_x, color=color,
        tooltip=["modelo", "pliegue", alt.Tooltip("valor:Q", format=".4f")])
    med = alt.Chart(res_g).mark_point(shape="diamond", size=260, filled=True, opacity=1).encode(
        y=eje_y, x=alt.X("media:Q"), color=color,
        tooltip=["modelo", alt.Tooltip("media:Q", format=".4f"), alt.Tooltip("de:Q", format=".4f", title="DE")])
    st.altair_chart((rango + pts + med).properties(height=390).configure_view(stroke=None)
                    .configure_axis(grid=True, gridColor="#EFE6DB", domain=False),
                    width="stretch")

    # Comparación pareada entre los dos primeros
    a, b = orden[0], orden[1]
    ancho = d.pivot(index="pliegue", columns="modelo", values="valor")
    dif = ancho[a] - ancho[b]
    c = st.columns(3)
    with c[0]:
        tarjeta("Mejor modelo", a, color=ACENTO, nota= f"{metrica} medio {res.media[0]:.4f} (DE {res.de[0]:.4f})")
    with c[1]:
        tarjeta("Segundo", b, f"{metrica} medio {res.media[1]:.4f} (DE {res.de[1]:.4f})")
    with c[2]:
        tarjeta("Diferencia pareada", f"{dif.mean():+.4f}",
                f"{a} gana en {(dif > 0).sum()} de {len(dif)} pliegues")
    st.write("")
    with st.expander("Tabla completa"):
        tabla = res.rename(columns={"modelo": "Modelo", "media": "Media", "de": "Desv. típica",
                                    "minimo": "Mínimo", "maximo": "Máximo"})
        st.dataframe(tabla.style.format({k: "{:.4f}" for k in tabla.columns[1:]}), hide_index=True,
                     width="stretch")
    reg = CV[~CV.metrica.isin(["AUC", "AP"])]
    if len(reg):
        with st.expander("Objetivo numérico: edad al diagnóstico"):
            t = reg.groupby(["modelo", "metrica"]).valor.mean().unstack().reset_index().rename(columns={"modelo": "Modelo"})
            st.dataframe(t.style.format({k: "{:.3f}" for k in t.columns[1:]}), hide_index=True,
                         width="stretch")
            st.caption("Media de los cinco pliegues. La edad se explica poco con estas variables; Ridge y Lasso no "
                       "mejoran la regresión lineal.")

# ----------------------------------------------------------------------------------------------------------------------
# 3. Clasificar una ficha
# ----------------------------------------------------------------------------------------------------------------------
FICHAS = fichas_sinteticas()
POR_ID = {f["id"]: f for f in FICHAS}


def fecha(s):
    return dt.date.fromisoformat(s)


def cargar_en_formulario(datos):
    ss = st.session_state
    ss.f_edad, ss.f_sexo, ss.f_regimen = datos["edad"], datos["sexo"], datos["regimen"]
    ss.f_area, ss.f_etnia, ss.f_region = datos["area"], datos["etnia"], datos["region"]
    ss.f_estrato = "Sin dato" if datos["estrato"] is None else datos["estrato"]
    ss.f_fecha_not = fecha(datos["fecha_notificacion"])
    ss.f_sin_fecha = datos["fecha_sintomas"] is None
    ss.f_fecha_sin = ss.f_fecha_not if ss.f_sin_fecha else fecha(datos["fecha_sintomas"])
    ss.f_grupos = list(datos["grupos"])
    ss.pop("resultado", None)


def al_elegir_ficha():
    cargar_en_formulario(POR_ID[st.session_state.ficha_id]["datos"])


def fila_del_contrato(d):
    """Convierte lo que se digita en la ficha a las columnas que espera el modelo. Devuelve (fila, notas)."""
    notas = []
    f_not = d["fecha_notificacion"] if isinstance(d["fecha_notificacion"], dt.date) else fecha(d["fecha_notificacion"])
    f_sin = d["fecha_sintomas"]
    if isinstance(f_sin, str):
        f_sin = fecha(f_sin)
    dias = None
    if f_sin is not None:
        dias = (f_not - f_sin).days
        if f_sin.month == 1 and f_sin.day == 1:
            dias, _ = None, notas.append("El 1 de enero como inicio de síntomas se trata como dato faltante.")
        elif dias < 0 or dias > DIAS_MAX:
            dias, _ = None, notas.append("El intervalo de síntomas no es válido y se trata como dato faltante.")
    if f_not.year > ANIO_FIN:
        notas.append(f"El modelo se entrenó con fichas de {ANIO_INICIO} a {ANIO_FIN}; {f_not.year} está fuera de ese rango.")
    fila = {"edad": d["edad"], "anio": f_not.year - ANIO_INICIO, "estrato_n": d["estrato"], "dias_sintomas": dias,
            **{g: int(g in d["grupos"]) for g in CONTRATO["columnas_binarias"]},
            "sexo": d["sexo"], "regimen": d["regimen"], "area": d["area"], "etnia": d["etnia"], "region": d["region"]}
    return fila, notas


if "f_edad" not in st.session_state:
    st.session_state.ficha_id = FICHAS[0]["id"]
    cargar_en_formulario(FICHAS[0]["datos"])

with t_ficha:
    form, salida = st.columns([1.1, 1], gap="large")
    with form:
        st.subheader("Ficha de notificación")
        st.selectbox("Cargar una ficha de prueba (sintética)", [f["id"] for f in FICHAS], key="ficha_id",
                     format_func=lambda i: f"{i} · {POR_ID[i]['titulo']}", on_change=al_elegir_ficha)
        a, b, c = st.columns(3)
        a.number_input("Edad (años)", 0, 100, key="f_edad")
        b.selectbox("Sexo", CATS["sexo"], key="f_sexo", format_func=ETIQ_SEXO.get)
        c.selectbox("Estrato", [1, 2, 3, 4, 5, 6, "Sin dato"], key="f_estrato")
        a, b = st.columns(2)
        a.selectbox("Régimen de salud", CATS["regimen"], key="f_regimen")
        b.selectbox("Área de residencia", CATS["area"], key="f_area")
        a, b = st.columns(2)
        a.selectbox("Región", CATS["region"], key="f_region")
        b.selectbox("Pertenencia étnica", CATS["etnia"], key="f_etnia")
        a, b = st.columns(2)
        a.date_input("Fecha de notificación", key="f_fecha_not", format="DD/MM/YYYY",
                     min_value=dt.date(ANIO_INICIO, 1, 1), max_value=dt.date(ANIO_FIN + 1, 12, 31))
        b.date_input("Inicio de síntomas", key="f_fecha_sin", format="DD/MM/YYYY",
                     min_value=dt.date(ANIO_INICIO - 10, 1, 1), max_value=dt.date(ANIO_FIN + 1, 12, 31),
                     disabled=st.session_state.f_sin_fecha)
        st.checkbox("La ficha no trae fecha de inicio de síntomas", key="f_sin_fecha")
        st.multiselect("Grupo poblacional", CONTRATO["columnas_binarias"], key="f_grupos",
                       format_func=ETIQ_GRUPOS.get, placeholder="Ninguno")
        if st.button("Clasificar ficha", type="primary", width="stretch"):
            ss = st.session_state
            digitado = {"edad": ss.f_edad, "sexo": ss.f_sexo, "regimen": ss.f_regimen, "area": ss.f_area,
                        "etnia": ss.f_etnia, "region": ss.f_region,
                        "estrato": None if ss.f_estrato == "Sin dato" else ss.f_estrato,
                        "fecha_notificacion": ss.f_fecha_not,
                        "fecha_sintomas": None if ss.f_sin_fecha else ss.f_fecha_sin, "grupos": ss.f_grupos}
            fila, notas = fila_del_contrato(digitado)
            pred, via, umbral = clasificar(fila)
            ss.resultado = {"fila": fila, "notas": notas, "pred": pred[0], "via": via, "umbral": umbral}

    with salida:
        st.subheader("Resultado")
        r = st.session_state.get("resultado")
        if not r:
            st.info("Elija una ficha de prueba o cambie los datos, y pulse **Clasificar ficha**.")
        else:
            p, u = r["pred"]["probabilidad"], r["umbral"]
            prioritaria = r["pred"]["ruta_prioritaria"]
            tono = AMBAR if prioritaria else VERDE
            st.markdown(f"""
<div class="resultado">
  <div class="rot">Probabilidad estimada de haber llegado hospitalizado</div>
  <div class="prob" style="color:{tono}">{100 * p:.1f} %</div>
  <div class="barra"><div class="lleno" style="width:{100 * p:.1f}%;background:{tono}"></div>
    <div class="umbral" style="left:{100 * u:.1f}%"><span>umbral {u:.2f}</span></div></div>
  <div class="pastilla" style="background:{tono}">{'RUTA PRIORITARIA' if prioritaria else 'TRÁMITE HABITUAL'}</div>
  <div class="nota" style="margin-top:.8rem;color:#695B50">
    {'La probabilidad alcanza el umbral: contacto el mismo día y verificación con la institución que notifica.'
     if prioritaria else 'La probabilidad queda por debajo del umbral: seguimiento por el trámite habitual.'}
  </div>
</div>""", unsafe_allow_html=True)
            st.caption(f"Calculado por: {r['via']}")
            for n in r["notas"]:
                st.warning(n)
            st.caption("Es una estimación a partir de casos parecidos del SIVIGILA. No es un diagnóstico ni una "
                       "afirmación sobre esta persona.")
            with st.expander("Lo que se envió al modelo y lo que respondió"):
                x, y = st.columns(2)
                x.markdown("**Fila con las columnas del contrato**")
                x.json(r["fila"])
                y.markdown("**Respuesta**")
                y.json(r["pred"])

    st.divider()
    st.subheader("Clasificar todas las fichas de prueba")
    st.markdown("Pasa las ocho fichas sintéticas por el modelo de una vez y muestra cómo las ordena.")
    if st.button("Clasificar el lote"):
        filas = [fila_del_contrato(f["datos"])[0] for f in FICHAS]
        pred, via, umbral = clasificar(filas)
        lote = pd.DataFrame({
            "Ficha": [f["id"] for f in FICHAS], "Descripción": [f["titulo"] for f in FICHAS],
            "Días con síntomas": [x["dias_sintomas"] for x in filas],
            "Probabilidad": [100 * q["probabilidad"] for q in pred],
            "Decisión": ["Ruta prioritaria" if q["ruta_prioritaria"] else "Trámite habitual" for q in pred],
        }).sort_values("Probabilidad", ascending=False)
        st.session_state.lote = (lote, via, umbral)
    if "lote" in st.session_state:
        lote, via, umbral = st.session_state.lote
        st.dataframe(lote, hide_index=True, width="stretch", column_config={
            "Probabilidad": st.column_config.ProgressColumn("Probabilidad", format="%.1f %%", min_value=0, max_value=100),
            "Días con síntomas": st.column_config.NumberColumn(format="%d")})
        n_pri = (lote["Decisión"] == "Ruta prioritaria").sum()
        st.caption(f"{n_pri} de {len(lote)} fichas pasan a ruta prioritaria con el umbral {umbral:.2f}. "
                   f"Calculado por: {via}")

# ----------------------------------------------------------------------------------------------------------------------
# 4. Servicio y límites
# ----------------------------------------------------------------------------------------------------------------------
with t_servicio:
    izq, der = st.columns(2, gap="large")
    with izq:
        st.subheader("Límites declarados")
        st.markdown(f"""
- **Depende de la fecha de síntomas.** Es la variable que más pesa, y su ausencia se concentra en ciertas
  instituciones: en parte el modelo aprende quién notifica.
- **No trata igual a todos los grupos.** La sensibilidad es menor en los más jóvenes y en el régimen contributivo.
- **Caduca.** Se entrenó con {ANIO_INICIO}–{ANIO_FIN} y debe revisarse al cerrar {CONTRATO['revisar_al_cerrar_anio']}.
- **Marca de más a propósito.** Con el umbral {UMBRAL:.2f} la precisión es {pct(MP['precision'])}: la mayoría de los
  marcados no estaba hospitalizada.
- **Asociación no es causa.** Ninguna variable prueba por qué alguien llega hospitalizado.
""")
        st.subheader("Desempeño en la prueba")
        st.dataframe(pd.DataFrame({
            "Métrica": ["AUC", "Sensibilidad", "Especificidad", "Precisión", "Casos de prueba"],
            "Valor": [f"{MP['AUC']:.3f}", pct(MP["sensibilidad"]), pct(MP["especificidad"]), pct(MP["precision"]),
                      miles(MP["casos"])]}), hide_index=True, width="stretch")
        st.caption("Cifras leídas del contrato guardado en el archivo .joblib. La prueba se usó una sola vez.")
    with der:
        st.subheader("Cómo viaja una ficha")
        st.markdown(f"""
<ol class="pasos">
<li>El formulario se convierte a las <b>{len(CONTRATO['columnas'])} columnas</b> del contrato.</li>
<li>El tablero llama a <code>predecir()</code> de <code>cargar_y_predecir.py</code>.</li>
<li>El <code>Pipeline</code> guardado imputa los faltantes, codifica y calcula la probabilidad.</li>
<li>Se compara con el umbral <b>{UMBRAL:.2f}</b> y se devuelve la decisión.</li>
</ol>""", unsafe_allow_html=True)
        st.subheader("Qué se despliega")
        st.markdown("""
- **Una sola aplicación:** este tablero, con el archivo del modelo y `cargar_y_predecir.py`.
- **Sin reentrenar:** el modelo se carga ya entrenado desde el `.joblib`.
- **Para otros sistemas:** `app.py` expone la misma función `predecir()` como servicio web (`/health` y `/predict`).
  El tablero no lo necesita.
""")
        with st.expander("Contrato del modelo"):
            st.json({k: v for k, v in CONTRATO.items() if k != "pipeline"})
        st.subheader("Equipo")
        st.markdown('<div class="equipo">' + "".join(f"<span>{n}</span>" for n in AUTORES) + "</div>",
                    unsafe_allow_html=True)
        st.caption("Machine Learning 2026-II · Universidad Tecnológica de Bolívar")

st.markdown(f'<div class="pie">Fuente de los datos: SIVIGILA, Instituto Nacional de Salud, evento 850 · '
            f'Modelo {CONTRATO["modelo"]} v{CONTRATO["version_modelo"]} · Demostración académica</div>',
            unsafe_allow_html=True)
