"""Servicio web del modelo de hospitalización al notificar VIH (SIVIGILA, evento 850).

Uso:  python app.py           (escucha en http://127.0.0.1:5000)
  GET  /health   -> estado del servicio y datos del contrato
  POST /predict  -> recibe un objeto JSON o una lista de objetos con las columnas del contrato
                    (null = dato faltante) y devuelve la probabilidad y la decisión con el umbral.
"""
from flask import Flask, jsonify, request

from cargar_y_predecir import ARCHIVO_MODELO, cargar, predecir

app = Flask(__name__)
CONTRATO = cargar(ARCHIVO_MODELO)


@app.get("/health")
def health():
    return jsonify({"estado": "ok", "modelo": CONTRATO["modelo"], "version_modelo": CONTRATO["version_modelo"],
                    "umbral": CONTRATO["umbral"], "entrenado_el": CONTRATO["entrenado_el"],
                    "columnas": CONTRATO["columnas"], "versiones": CONTRATO["versiones"]})


@app.post("/predict")
def predict():
    datos = request.get_json(silent=True)
    if not isinstance(datos, (dict, list)) or not datos:
        return jsonify({"error": "Se espera un objeto JSON o una lista de objetos con las columnas del contrato"}), 400
    try:
        resultados = predecir(CONTRATO, datos)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"version_modelo": CONTRATO["version_modelo"], "umbral": CONTRATO["umbral"],
                    "predicciones": resultados})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
