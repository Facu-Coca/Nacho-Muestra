"""Mide qué tan bien adivina un modelo (Ivo, etapa 2).

Pasa por el modelo dos grupos de dibujos y muestra cuánto acierta:

  1. Dibujos propios: los que se guardaron jugando en la página (datos_muestra/,
     una carpeta por categoría). Se preparan igual que en el juego, con
     procesamiento.a_28x28, así que el resultado es el mismo que vería un visitante.
  2. Prueba de Quick, Draw!: los últimos dibujos de cada archivo datos/<categoria>.npy,
     los mismos que usa entrenar.py para probar (la red nunca los vio al entrenar).
     Si no están descargados, muestra el resultado que quedó guardado en el modelo.

Para cada grupo muestra:
  - % de aciertos total y por categoría,
  - % de veces que la correcta quedó entre las 3 primeras,
  - qué pares se confunden más (con ejemplos, para avisar a Facu y Vicente).

Al final dice si se puede dar el OK (más de 85% en dibujos propios) y deja una
fila lista para copiar en pruebas/resultados.md.

Uso (desde la carpeta del repo, con el entorno virtual activo):
  python pruebas/evaluar.py
  python pruebas/evaluar.py --modelo otro_modelo.pt
  python pruebas/evaluar.py --quickdraw 0        # no evaluar Quick, Draw!
"""

import argparse
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import numpy as np
import torch
from PIL import Image

# Para poder importar los archivos de Facu (modelo.py, procesamiento.py) que están en la raíz.
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import modelo  # noqa: E402
import procesamiento  # noqa: E402

META_PROPIOS = 0.85     # condición para dar el OK
META_QUICKDRAW = 0.90
META_TOP3 = 0.95
DIBUJOS_RECOMENDADOS = 300


# ---------- Cargar dibujos ----------

def cargar_propios(carpeta, categorias):
    """Lee datos_muestra/<categoria en inglés>/*.png.

    Devuelve (arrays 28x28, índice de la categoría correcta, ruta de cada archivo, avisos).
    """
    indice_de = {ingles: i for i, (ingles, _) in enumerate(categorias)}
    arrays, correctas, rutas, avisos = [], [], [], []
    if not carpeta.exists():
        return arrays, correctas, rutas, [f"No existe {carpeta}: todavía no se guardó ningún dibujo."]

    for subcarpeta in sorted(p for p in carpeta.iterdir() if p.is_dir()):
        if subcarpeta.name not in indice_de:
            avisos.append(f"'{subcarpeta.name}' no es una categoría de este modelo: se saltea.")
            continue
        for archivo in sorted(subcarpeta.glob("*.png")):
            try:
                with Image.open(archivo) as imagen:
                    array = procesamiento.a_28x28(imagen)
            except Exception as e:
                avisos.append(f"No se pudo abrir {archivo.name}: {e}")
                continue
            if array is None:  # lienzo vacío: el juego tampoco lo tiene en cuenta
                avisos.append(f"{subcarpeta.name}/{archivo.name} está vacío: se saltea.")
                continue
            arrays.append(array)
            correctas.append(indice_de[subcarpeta.name])
            rutas.append(archivo.relative_to(carpeta).as_posix())
    return arrays, correctas, rutas, avisos


def cargar_quickdraw(categorias, por_categoria):
    """Últimos `por_categoria` dibujos de cada datos/<ingles>.npy (los mismos que usa entrenar.py
    para probar). Devuelve (arrays, correctas) o None si falta algún archivo."""
    carpeta = RAIZ / "datos"
    arrays, correctas = [], []
    for i, (ingles, _) in enumerate(categorias):
        ruta = carpeta / f"{ingles}.npy"
        if not ruta.exists():
            return None
        todos = np.load(ruta, mmap_mode="r")
        arrays.append(np.array(todos[-por_categoria:]))
        correctas.append(np.full(min(por_categoria, len(todos)), i))
    return np.concatenate(arrays), np.concatenate(correctas)


# ---------- Predecir y medir ----------

@torch.no_grad()
def predecir_top3(red, arrays, lote=1024):
    """Devuelve, para cada dibujo, los índices de las 3 categorías más probables (la primera es la respuesta)."""
    resultado = []
    for i in range(0, len(arrays), lote):
        x = torch.as_tensor(np.asarray(arrays[i:i + lote]), dtype=torch.float32)
        x = x.reshape(-1, 1, modelo.LADO, modelo.LADO) / 255.0
        resultado.append(red(x).topk(3, dim=1).indices)
    return torch.cat(resultado).numpy()


def medir(categorias, correctas, top3, rutas=None, titulo=""):
    """Imprime los resultados de un grupo de dibujos y devuelve (% aciertos, % top-3)."""
    nombres = [castellano for _, castellano in categorias]
    correctas = np.asarray(correctas)
    respuestas = top3[:, 0]
    acerto = respuestas == correctas
    en_top3 = (top3 == correctas[:, None]).any(axis=1)
    total = len(correctas)

    print(f"\n=== {titulo} ({total} dibujos) ===")
    print(f"Aciertos:                        {acerto.mean():.1%}  ({acerto.sum()} de {total})")
    print(f"Correcta entre las 3 primeras:   {en_top3.mean():.1%}  ({en_top3.sum()} de {total})")

    # Por categoría, de peor a mejor. Solo las que tienen dibujos.
    print("\nPor categoría (de peor a mejor):")
    filas = []
    for i, nombre in enumerate(nombres):
        de_esta = correctas == i
        if de_esta.any():
            filas.append((acerto[de_esta].mean(), nombre, acerto[de_esta].sum(), de_esta.sum()))
    for porcentaje, nombre, ok, cuantos in sorted(filas):
        print(f"  {nombre:<11} {porcentaje:>6.1%}  ({ok} de {cuantos})")
    sin_dibujos = [n for i, n in enumerate(nombres) if not (correctas == i).any()]
    if sin_dibujos:
        print(f"  Sin dibujos: {', '.join(sin_dibujos)}")

    # Pares que más se confunden: (lo que se pidió, lo que creyó la IA).
    errores = ~acerto
    pares = Counter(zip(correctas[errores], respuestas[errores]))
    ejemplos = defaultdict(list)
    if rutas is not None:
        for indice in np.flatnonzero(errores):
            ejemplos[(correctas[indice], respuestas[indice])].append(rutas[indice])

    print("\nLo que más confunde (pedido -> lo que creyó la IA):")
    if not pares:
        print("  Nada: acertó todos.")
    for (pedido, creyo), veces in pares.most_common(8):
        de_pedido = int((correctas == pedido).sum())
        linea = f"  {nombres[pedido]} -> {nombres[creyo]}: {veces} de {de_pedido} ({veces / de_pedido:.0%})"
        if ejemplos[(pedido, creyo)]:
            linea += f"   ej: {', '.join(ejemplos[(pedido, creyo)][:2])}"
        print(linea)

    return float(acerto.mean()), float(en_top3.mean())


# ---------- Programa ----------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modelo", default=str(RAIZ / "modelo.pt"), help="archivo del modelo (por defecto modelo.pt)")
    parser.add_argument("--muestra", default=str(RAIZ / "datos_muestra"), help="carpeta con los dibujos propios")
    parser.add_argument("--quickdraw", type=int, default=500,
                        help="dibujos de prueba de Quick, Draw! por categoría (0 = no evaluar)")
    args = parser.parse_args()

    red, categorias, info = modelo.cargar(args.modelo)
    version = Path(args.modelo).name
    print(f"Modelo: {version}  |  entrenado: {info.get('fecha', '?')}"
          + ("  |  PROVISORIO" if info.get("provisorio") else ""))
    if info.get("con_muestra"):
        print("OJO: este modelo se entrenó sumando los dibujos de datos_muestra/. Si son los mismos que se\n"
              "evalúan acá, el % de dibujos propios va a salir más alto de lo real (ya los conoce).")

    # 1. Dibujos propios
    arrays, correctas, rutas, avisos = cargar_propios(Path(args.muestra), categorias)
    for aviso in avisos:
        print(f"Aviso: {aviso}")
    propios = top3_propios = None
    if arrays:
        propios, top3_propios = medir(categorias, correctas, predecir_top3(red, arrays), rutas,
                                      f"Dibujos propios ({Path(args.muestra).name}/)")
    else:
        print("\nNo hay dibujos propios para evaluar. Guardá dibujos jugando en la página.")

    # 2. Prueba de Quick, Draw!
    quickdraw = None
    if args.quickdraw > 0:
        datos = cargar_quickdraw(categorias, args.quickdraw)
        if datos is not None:
            x, y = datos
            quickdraw, _ = medir(categorias, y, predecir_top3(red, x), None,
                                 f"Prueba Quick, Draw! ({args.quickdraw} por categoría)")
        else:
            guardado = info.get("metricas", {}).get("prueba_quickdraw", {})
            if guardado:
                quickdraw = guardado["aciertos"]
                print(f"\n=== Prueba Quick, Draw! (dato guardado en el modelo, no hay datos/ descargado) ===")
                print(f"Aciertos: {guardado['aciertos']:.1%}   Correcta entre las 3 primeras: {guardado['top3']:.1%}")
            else:
                print("\nNo hay datos/ de Quick, Draw! ni resultado guardado en el modelo.")

    # 3. Veredicto
    print("\n=== Veredicto ===")
    if quickdraw is not None:
        print(f"Quick, Draw!:     {quickdraw:.1%}  (meta > {META_QUICKDRAW:.0%})"
              + ("  OK" if quickdraw > META_QUICKDRAW else "  no llega"))
    if propios is not None:
        print(f"Dibujos propios:  {propios:.1%}  (meta > {META_PROPIOS:.0%})"
              + ("  OK" if propios > META_PROPIOS else "  no llega"))
        print(f"Top-3 propios:    {top3_propios:.1%}  (meta > {META_TOP3:.0%})"
              + ("  OK" if top3_propios > META_TOP3 else "  no llega"))
        if len(correctas) < DIBUJOS_RECOMENDADOS:
            print(f"Todavía hay pocos dibujos ({len(correctas)}; la meta es {DIBUJOS_RECOMENDADOS}, unos 12 por "
                  "categoría): el resultado puede cambiar bastante.")
        dar_ok = propios > META_PROPIOS and len(correctas) >= DIBUJOS_RECOMENDADOS
        print("¿Dar el OK?      " + ("SÍ" if dar_ok else "NO"))
    else:
        dar_ok = False

    # 4. Fila para pruebas/resultados.md
    def pct(valor):
        return f"{valor:.1%}" if valor is not None else ""
    print("\nFila para pruebas/resultados.md:")
    print(f"| {date.today()} | {version} ({info.get('fecha', '?')}"
          + (", provisorio" if info.get("provisorio") else "") + ") "
          f"| {info.get('por_categoria', '')} | {pct(quickdraw)} | {pct(propios)} | {pct(top3_propios)} "
          f"| {len(correctas)} | {'Sí' if dar_ok else 'No'} | |")


if __name__ == "__main__":
    main()
