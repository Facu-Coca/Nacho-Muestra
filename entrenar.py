"""Entrena la red con los dibujos de Quick, Draw! (y opcionalmente con los de la muestra).

Uso:
  python entrenar.py                # entrenamiento completo (20.000 por categoria)
  python entrenar.py --rapido       # modelo provisorio en un par de minutos
  python entrenar.py --con-muestra  # suma los dibujos guardados en datos_muestra/

Al terminar guarda modelo.pt y muestra:
  - % de aciertos con dibujos de prueba que la red nunca vio,
  - % de veces que la correcta quedo entre las 3 primeras,
  - aciertos por categoria y que pares confunde mas.
"""

import argparse
import math
import os
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from descargar import CARPETA_DATOS, leer_categorias
from modelo import LADO, RedDibujos, cargar, guardar
from procesamiento import a_28x28

RAIZ = Path(__file__).parent
CARPETA_MUESTRA = RAIZ / "datos_muestra"


# ---------- Datos ----------

def cargar_quickdraw(categorias, por_categoria, prueba):
    """Devuelve (x_entrenamiento, y_entrenamiento, x_prueba, y_prueba) como arrays uint8 / int64.

    Los de prueba salen del final de cada archivo, asi nunca se mezclan con los de entrenamiento.
    """
    xs_ent, ys_ent, xs_pru, ys_pru = [], [], [], []
    for indice, (ingles, _) in enumerate(categorias):
        ruta = CARPETA_DATOS / f"{ingles}.npy"
        if not ruta.exists():
            raise SystemExit(f"Falta {ruta}. Corre primero: python descargar.py")
        todos = np.load(ruta, mmap_mode="r")
        if len(todos) < por_categoria + prueba:
            raise SystemExit(f"{ingles} tiene {len(todos)} dibujos, no alcanza para {por_categoria}+{prueba}")
        xs_ent.append(np.array(todos[:por_categoria]))
        xs_pru.append(np.array(todos[-prueba:]))
        ys_ent.append(np.full(por_categoria, indice))
        ys_pru.append(np.full(prueba, indice))
    return (np.concatenate(xs_ent), np.concatenate(ys_ent),
            np.concatenate(xs_pru), np.concatenate(ys_pru))


def cargar_muestra(categorias):
    """Lee los dibujos guardados en la muestra (datos_muestra/<categoria>/*.png) y los procesa."""
    xs, ys = [], []
    for indice, (ingles, _) in enumerate(categorias):
        carpeta = CARPETA_MUESTRA / ingles
        for archivo in sorted(carpeta.glob("*.png")) if carpeta.exists() else []:
            array = a_28x28(Image.open(archivo))
            if array is not None:
                xs.append(array.reshape(-1))
                ys.append(indice)
    if not xs:
        return np.zeros((0, LADO * LADO), np.uint8), np.zeros(0, np.int64)
    return np.stack(xs), np.array(ys)


# ---------- Aumentacion: rotar, mover, agrandar y achicar un poco ----------

def aumentar(x):
    """x: tensor (n, 1, 28, 28). Aplica a cada dibujo una transformacion al azar distinta."""
    n, d = x.shape[0], x.device
    angulo = (torch.rand(n, device=d) * 2 - 1) * math.radians(12)
    escala = 1 + (torch.rand(n, device=d) * 2 - 1) * 0.15
    mover = (torch.rand(n, 2, device=d) * 2 - 1) * 0.12
    cos, sen = torch.cos(angulo) / escala, torch.sin(angulo) / escala
    matriz = torch.stack([torch.stack([cos, -sen, mover[:, 0]], 1),
                          torch.stack([sen, cos, mover[:, 1]], 1)], 1)
    grilla = F.affine_grid(matriz, x.shape, align_corners=False)
    x = F.grid_sample(x, grilla, align_corners=False, padding_mode="zeros")

    # Trazo mas grueso o mas fino al azar, porque cada persona dibuja distinto.
    sorteo = torch.rand(n, 1, 1, 1, device=d)
    engrosado = torch.maximum(x, 0.6 * F.max_pool2d(x, 3, stride=1, padding=1))
    afinado = 0.5 * (x - F.max_pool2d(-x, 3, stride=1, padding=1))
    x = torch.where(sorteo < 0.25, engrosado, torch.where(sorteo < 0.4, afinado, x))
    return x


# ---------- Evaluacion ----------

@torch.no_grad()
def evaluar(red, x, y, lote=2048):
    red.eval()
    dispositivo = next(red.parameters()).device
    predicciones, top3 = [], []
    for i in range(0, len(x), lote):
        entrada = torch.as_tensor(x[i:i + lote], dtype=torch.float32).reshape(-1, 1, LADO, LADO) / 255.0
        puntajes = red(entrada.to(dispositivo)).cpu()
        predicciones.append(puntajes.argmax(1))
        top3.append(puntajes.topk(3, dim=1).indices)
    predicciones = torch.cat(predicciones).numpy()
    top3 = torch.cat(top3).numpy()
    return predicciones, (top3 == y[:, None]).any(1)


def resumen(categorias, y, predicciones, en_top3, titulo):
    n = len(categorias)
    confusion = np.zeros((n, n), dtype=np.int64)
    np.add.at(confusion, (y, predicciones), 1)
    acierto = float((predicciones == y).mean())
    acierto_top3 = float(en_top3.mean())

    print(f"\n=== {titulo} ({len(y)} dibujos) ===")
    print(f"Aciertos: {acierto:.1%}   Correcta entre las 3 primeras: {acierto_top3:.1%}")
    print("Por categoria (de peor a mejor):")
    por_categoria = confusion.diagonal() / confusion.sum(1).clip(min=1)
    for i in np.argsort(por_categoria):
        print(f"  {categorias[i][1]:<11} {por_categoria[i]:.1%}")

    pares = []
    for i in range(n):
        for j in range(n):
            if i != j and confusion[i, j]:
                pares.append((confusion[i, j] / confusion[i].sum(), categorias[i][1], categorias[j][1]))
    pares.sort(reverse=True)
    print("Lo que mas confunde (pedido -> lo que creyo):")
    for proporcion, pedido, creyo in pares[:8]:
        aviso = "   <- avisar a Vicente" if proporcion > 0.05 else ""
        print(f"  {pedido} -> {creyo}: {proporcion:.1%}{aviso}")

    return {
        "aciertos": round(acierto, 4),
        "top3": round(acierto_top3, 4),
        "por_categoria": {categorias[i][1]: round(float(por_categoria[i]), 4) for i in range(n)},
        "confusiones": [{"pedido": p, "creyo": c, "proporcion": round(float(x), 4)} for x, p, c in pares[:10]],
    }


# ---------- Entrenamiento ----------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--por-categoria", type=int, default=20000)
    parser.add_argument("--prueba", type=int, default=2000)
    parser.add_argument("--epocas", type=int, default=6)
    parser.add_argument("--lote", type=int, default=256)
    parser.add_argument("--aprendizaje", type=float, default=0.003)
    parser.add_argument("--rapido", action="store_true", help="modelo provisorio: 3000 por categoria y 2 epocas")
    parser.add_argument("--con-muestra", action="store_true", help="sumar los dibujos de datos_muestra/")
    parser.add_argument("--repetir-muestra", type=int, default=20,
                        help="cuantas veces se repite cada dibujo de la muestra (son pocos y valen mucho)")
    parser.add_argument("--desde", help="arrancar desde los pesos de un modelo ya entrenado")
    parser.add_argument("--salida", default="modelo.pt")
    args = parser.parse_args()
    if args.rapido:
        args.por_categoria, args.prueba, args.epocas = 3000, 500, 2

    torch.manual_seed(0)
    torch.set_num_threads(os.cpu_count() or 4)
    categorias = leer_categorias()
    print(f"{len(categorias)} categorias. Cargando dibujos...")
    x_ent, y_ent, x_pru, y_pru = cargar_quickdraw(categorias, args.por_categoria, args.prueba)

    x_mue = y_mue = None
    if args.con_muestra:
        x_mue, y_mue = cargar_muestra(categorias)
        print(f"Dibujos de la muestra: {len(x_mue)} (cada uno se repite {args.repetir_muestra} veces)")
        if len(x_mue):
            x_ent = np.concatenate([x_ent] + [x_mue] * args.repetir_muestra)
            y_ent = np.concatenate([y_ent] + [y_mue] * args.repetir_muestra)
    print(f"Entrenamiento: {len(x_ent)} dibujos. Prueba: {len(x_pru)} dibujos.")

    red = RedDibujos(len(categorias))
    if args.desde:
        anterior, categorias_anteriores, _ = cargar(args.desde)
        if categorias_anteriores != categorias:
            raise SystemExit("Las categorias de categorias.txt no coinciden con las del modelo de --desde")
        red.load_state_dict(anterior.state_dict())

    # Si hay placa de video NVIDIA se usa (mucho mas rapido); si no, el procesador.
    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Entrenando con: {torch.cuda.get_device_name(0) if dispositivo == 'cuda' else 'procesador (CPU)'}")
    red = red.to(dispositivo, memory_format=torch.channels_last)  # channels_last acelera las convoluciones
    x_ent_t = torch.as_tensor(x_ent).reshape(-1, 1, LADO, LADO).to(dispositivo)
    y_ent_t = torch.as_tensor(y_ent, dtype=torch.long).to(dispositivo)
    pasos_por_epoca = math.ceil(len(x_ent) / args.lote)
    optimizador = torch.optim.AdamW(red.parameters(), lr=args.aprendizaje, weight_decay=1e-4)
    planificador = torch.optim.lr_scheduler.OneCycleLR(
        optimizador, max_lr=args.aprendizaje, total_steps=args.epocas * pasos_por_epoca)

    for epoca in range(1, args.epocas + 1):
        red.train()
        inicio = time.time()
        orden = torch.randperm(len(x_ent_t), device=dispositivo)
        perdida_total = 0.0
        for paso in range(pasos_por_epoca):
            indices = orden[paso * args.lote:(paso + 1) * args.lote]
            x = aumentar(x_ent_t[indices].float() / 255.0).contiguous(memory_format=torch.channels_last)
            perdida = F.cross_entropy(red(x), y_ent_t[indices], label_smoothing=0.05)
            optimizador.zero_grad()
            perdida.backward()
            optimizador.step()
            planificador.step()
            perdida_total += perdida.item()
        predicciones, _ = evaluar(red, x_pru, y_pru)
        print(f"Epoca {epoca}/{args.epocas}: error {perdida_total / pasos_por_epoca:.3f}, "
              f"aciertos en prueba {(predicciones == y_pru).mean():.1%} ({time.time() - inicio:.0f} s)")

    predicciones, en_top3 = evaluar(red, x_pru, y_pru)
    metricas = {"prueba_quickdraw": resumen(categorias, y_pru, predicciones, en_top3, "Prueba Quick, Draw!")}
    if x_mue is not None and len(x_mue):
        predicciones, en_top3 = evaluar(red, x_mue, y_mue)
        metricas["dibujos_muestra"] = resumen(
            categorias, y_mue, predicciones, en_top3, "Dibujos de la muestra (ojo: tambien se usaron para entrenar)")

    info = {
        "fecha": datetime.now().isoformat(timespec="minutes"),
        "provisorio": args.rapido,
        "por_categoria": args.por_categoria,
        "epocas": args.epocas,
        "con_muestra": args.con_muestra,
        "metricas": metricas,
    }
    guardar(args.salida, red.cpu(), categorias, info)
    print(f"\nGuardado en {args.salida}")


if __name__ == "__main__":
    main()
