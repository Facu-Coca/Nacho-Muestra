"""Prepara el dibujo del lienzo para que la IA lo vea igual que los de Quick, Draw!.

Los dibujos de Quick, Draw! (archivos .npy) son imagenes de 28x28 con:
  - trazo blanco sobre fondo negro,
  - el dibujo recortado y centrado, con el lado mas largo ocupando 26 pixeles
    (queda 1 pixel de margen),
  - un trazo grueso, de unos 2 pixeles, con bordes suaves.

Este archivo hace lo mismo con el dibujo que manda la pagina. Es lo que mas
influye en que la IA acierte con dibujos de gente real.
"""

import base64
import io

import numpy as np
from PIL import Image, ImageFilter

LADO = 28            # tamano final que ve la IA
FACTOR = 9           # trabajamos a 28*9 = 252 px y al final achicamos
GROSOR_OBJETIVO = 1.3  # grosor del trazo en 28x28 (en pixeles); calibrado comparando con los .npy
UMBRAL_TINTA = 40    # de 0 a 255: cuanto tiene que oscurecer un pixel para contar como trazo
MIN_PIXELES = 15     # menos pixeles de trazo que esto = lienzo vacio


def decodificar(imagen_base64):
    """Convierte el texto base64 que manda la pagina (con o sin 'data:image/png;base64,') en una imagen."""
    if "," in imagen_base64[:100]:
        imagen_base64 = imagen_base64.split(",", 1)[1]
    return Image.open(io.BytesIO(base64.b64decode(imagen_base64)))


def a_escala_de_grises(imagen):
    """Imagen del lienzo (fondo blanco o transparente, trazo oscuro) -> array con trazo blanco sobre negro."""
    if imagen.mode in ("RGBA", "LA", "P"):
        imagen = imagen.convert("RGBA")
        fondo = Image.new("RGBA", imagen.size, (255, 255, 255, 255))
        imagen = Image.alpha_composite(fondo, imagen)
    gris = np.asarray(imagen.convert("L"), dtype=np.uint8)
    return 255 - gris


def grosor_del_trazo(mascara):
    """Estima el grosor del trazo en pixeles: area / (borde / 2).

    Un trazo de largo L y grosor g ocupa L*g pixeles y tiene unos 2*L pixeles de borde.
    """
    interior = mascara.copy()
    interior[1:, :] &= mascara[:-1, :]
    interior[:-1, :] &= mascara[1:, :]
    interior[:, 1:] &= mascara[:, :-1]
    interior[:, :-1] &= mascara[:, 1:]
    borde = int((mascara & ~interior).sum())
    return 2 * mascara.sum() / max(borde, 1)


def a_28x28(imagen):
    """Imagen del lienzo -> array uint8 de 28x28 como los de Quick, Draw!. Devuelve None si esta vacio."""
    tinta = a_escala_de_grises(imagen)
    mascara = tinta > UMBRAL_TINTA
    if mascara.sum() < MIN_PIXELES:
        return None

    # 1. Recortar al rectangulo que contiene el dibujo.
    filas = np.flatnonzero(mascara.any(axis=1))
    columnas = np.flatnonzero(mascara.any(axis=0))
    y0, y1, x0, x1 = filas[0], filas[-1] + 1, columnas[0], columnas[-1] + 1
    recorte = tinta[y0:y1, x0:x1]
    alto, ancho = recorte.shape

    # 2. Escalar para que el lado mas largo mida 26 px (en la escala de 28) y centrar.
    grande = LADO * FACTOR
    escala = (LADO - 2) * FACTOR / max(alto, ancho)
    nuevo_ancho = max(1, round(ancho * escala))
    nuevo_alto = max(1, round(alto * escala))
    recorte = Image.fromarray(recorte).resize((nuevo_ancho, nuevo_alto), Image.BILINEAR)
    lienzo = Image.new("L", (grande, grande), 0)
    lienzo.paste(recorte, ((grande - nuevo_ancho) // 2, (grande - nuevo_alto) // 2))

    # 3. Emparejar el grosor del trazo con el de Quick, Draw!.
    grosor_actual = grosor_del_trazo(mascara[y0:y1, x0:x1]) * escala
    diferencia = round(GROSOR_OBJETIVO * FACTOR - grosor_actual)
    if diferencia >= 2:
        lienzo = lienzo.filter(ImageFilter.MaxFilter(diferencia // 2 * 2 + 1))   # engrosar
    elif diferencia <= -2:
        lienzo = lienzo.filter(ImageFilter.MinFilter(-diferencia // 2 * 2 + 1))  # afinar

    # 4. Achicar a 28x28 promediando (da bordes suaves como los originales).
    chica = np.asarray(lienzo.resize((LADO, LADO), Image.BOX), dtype=np.float32)
    if chica.max() > 0:
        chica = chica * (255.0 / chica.max())
    return chica.clip(0, 255).astype(np.uint8)


def a_png_base64(array_28x28):
    """Array de 28x28 -> 'data:image/png;base64,...' para mostrar en la pestana 'Como funciona'."""
    buffer = io.BytesIO()
    Image.fromarray(array_28x28).save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
