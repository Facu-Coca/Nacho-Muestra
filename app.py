"""Servidor del juego. Corre en la misma compu, sin internet.

Uso:  python app.py   y abrir http://127.0.0.1:5000

Rutas (el contrato con la pagina esta explicado en README.md):
  GET  /              la pagina del juego (templates/index.html)
  GET  /categorias    lista de cosas que se pueden pedir
  POST /predecir      recibe el dibujo y devuelve las 3 opciones mas probables
  POST /guardar       guarda el dibujo terminado con la categoria que se pidio
  GET  /estadisticas  cuantos dibujos se jugaron, cuanto acierta y que confunde
"""

import csv
import threading
from collections import Counter
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

import modelo
import procesamiento

RAIZ = Path(__file__).parent
CARPETA_MUESTRA = RAIZ / "datos_muestra"
REGISTRO = CARPETA_MUESTRA / "registro.csv"
COLUMNAS = ["fecha", "pedida", "creyo", "adivino", "archivo"]

app = Flask(__name__)
red, categorias, info_modelo = modelo.cargar(RAIZ / "modelo.pt")
nombres = [castellano for _, castellano in categorias]
ingles_de = {castellano: ingles for ingles, castellano in categorias}
candado = threading.Lock()  # para que dos pedidos no escriban el registro a la vez


def error(mensaje, codigo=400):
    return jsonify({"error": mensaje}), codigo


def leer_dibujo():
    """Saca el dibujo del pedido JSON. Devuelve (imagen, array_28x28) o lanza ValueError."""
    datos = request.get_json(silent=True) or {}
    texto = datos.get("imagen")
    if not texto:
        raise ValueError("Falta 'imagen' (el lienzo en base64)")
    try:
        imagen = procesamiento.decodificar(texto)
        imagen.load()
    except Exception:
        raise ValueError("'imagen' no es una imagen valida en base64")
    return imagen, procesamiento.a_28x28(imagen)


def top3(array_28x28):
    probabilidades = modelo.predecir(red, array_28x28)
    orden = sorted(range(len(nombres)), key=lambda i: probabilidades[i], reverse=True)[:3]
    return [{"categoria": nombres[i], "prob": round(probabilidades[i], 4)} for i in orden]


@app.get("/")
def inicio():
    return render_template("index.html")


@app.get("/categorias")
def ver_categorias():
    return jsonify(nombres)


@app.post("/predecir")
def predecir():
    try:
        _, array = leer_dibujo()
    except ValueError as e:
        return error(str(e))
    if array is None:  # lienzo vacio
        return jsonify({"top": [], "vista_ia": None, "vacio": True})
    return jsonify({"top": top3(array), "vista_ia": procesamiento.a_png_base64(array), "vacio": False})


@app.post("/guardar")
def guardar():
    datos = request.get_json(silent=True) or {}
    pedida = datos.get("categoria")
    if pedida not in ingles_de:
        return error(f"'categoria' tiene que ser una de: {', '.join(nombres)}")
    try:
        imagen, array = leer_dibujo()
    except ValueError as e:
        return error(str(e))
    if array is None:
        return jsonify({"guardado": False, "motivo": "lienzo vacio"})

    creyo = top3(array)[0]["categoria"]
    # Si la pagina dice si adivino durante el juego, vale eso; si no, se usa el dibujo final.
    adivino = bool(datos["adivino"]) if "adivino" in datos else creyo == pedida

    ahora = datetime.now()
    carpeta = CARPETA_MUESTRA / ingles_de[pedida]
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / f"{ahora:%Y%m%d-%H%M%S-%f}.png"
    imagen.save(archivo)

    with candado:
        nuevo = not REGISTRO.exists()
        with open(REGISTRO, "a", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f)
            if nuevo:
                escritor.writerow(COLUMNAS)
            escritor.writerow([ahora.isoformat(timespec="seconds"), pedida, creyo,
                               int(adivino), archivo.relative_to(CARPETA_MUESTRA).as_posix()])
    return jsonify({"guardado": True, "creyo": creyo, "adivino": adivino})


@app.get("/estadisticas")
def estadisticas():
    filas = []
    if REGISTRO.exists():
        with candado, open(REGISTRO, newline="", encoding="utf-8") as f:
            filas = list(csv.DictReader(f))
    total = len(filas)
    aciertos = sum(f["adivino"] == "1" for f in filas)

    por_categoria = {}
    for nombre in nombres:
        de_esta = [f for f in filas if f["pedida"] == nombre]
        if de_esta:
            ok = sum(f["adivino"] == "1" for f in de_esta)
            por_categoria[nombre] = {"jugados": len(de_esta), "aciertos": ok,
                                     "porcentaje": round(ok / len(de_esta), 4)}

    confusiones = Counter((f["pedida"], f["creyo"]) for f in filas
                          if f["adivino"] != "1" and f["creyo"] != f["pedida"])
    prueba = info_modelo.get("metricas", {}).get("prueba_quickdraw", {})
    return jsonify({
        "dibujos_jugados": total,
        "aciertos": aciertos,
        "porcentaje_aciertos": round(aciertos / total, 4) if total else None,
        "por_categoria": por_categoria,
        "mas_confundidas": [{"pedida": p, "creyo": c, "veces": n} for (p, c), n in confusiones.most_common(5)],
        "modelo": {"fecha": info_modelo.get("fecha"), "provisorio": info_modelo.get("provisorio"),
                   "aciertos_prueba_quickdraw": prueba.get("aciertos"), "top3_prueba_quickdraw": prueba.get("top3")},
    })


if __name__ == "__main__":
    print(f"Modelo cargado: {len(nombres)} categorias, entrenado {info_modelo.get('fecha')}"
          + (" (PROVISORIO)" if info_modelo.get("provisorio") else ""))
    print("Abri http://127.0.0.1:5000 en el navegador")
    app.run(host="127.0.0.1", port=5000, threaded=True)
