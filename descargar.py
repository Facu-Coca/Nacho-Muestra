"""Baja de Google los dibujos de Quick, Draw! de cada categoria de categorias.txt.

Cada archivo .npy tiene todos los dibujos de una categoria ya convertidos
a imagenes de 28x28 (unos 100.000 a 150.000 dibujos, 80 a 150 MB por archivo).
Se guardan en datos/, que no se sube al repo.

Uso:  python descargar.py
"""

import sys
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).parent
CARPETA_DATOS = RAIZ / "datos"
URL_BASE = "https://storage.googleapis.com/quickdraw_dataset/full/numpy_bitmap/"


def leer_categorias(ruta=RAIZ / "categorias.txt"):
    """Devuelve una lista de (nombre_ingles, nombre_castellano)."""
    categorias = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        ingles, _, castellano = linea.partition(",")
        categorias.append((ingles.strip(), castellano.strip() or ingles.strip()))
    return categorias


def descargar(ingles):
    destino = CARPETA_DATOS / f"{ingles}.npy"
    if destino.exists():
        print(f"  {ingles}: ya estaba, la salteo")
        return
    url = URL_BASE + urllib.parse.quote(ingles) + ".npy"
    temporal = destino.with_suffix(".npy.parcial")
    with urllib.request.urlopen(url) as respuesta, open(temporal, "wb") as archivo:
        total = int(respuesta.headers.get("Content-Length", 0))
        bajado = 0
        while bloque := respuesta.read(1 << 20):
            archivo.write(bloque)
            bajado += len(bloque)
            if total:
                print(f"\r  {ingles}: {bajado * 100 // total}% de {total // 2**20} MB", end="")
    temporal.rename(destino)
    print()


def main():
    CARPETA_DATOS.mkdir(exist_ok=True)
    categorias = leer_categorias()
    print(f"Descargando {len(categorias)} categorias en {CARPETA_DATOS}")
    fallaron = []
    for ingles, _ in categorias:
        try:
            descargar(ingles)
        except Exception as error:
            print(f"\n  {ingles}: ERROR {error} (revisar que el nombre este bien escrito)")
            fallaron.append(ingles)
    if fallaron:
        print("Fallaron:", ", ".join(fallaron))
        sys.exit(1)
    print("Listo.")


if __name__ == "__main__":
    main()
