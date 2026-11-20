"""La red neuronal: una CNN (red neuronal convolucional) para dibujos de 28x28.

Recorrido de un dibujo por la red:
  imagen 28x28
  -> bloque 1: 32 filtros  (detecta lineas y curvas)        -> 14x14
  -> bloque 2: 64 filtros  (combina en esquinas, circulos)  -> 7x7
  -> bloque 3: 128 filtros (formas grandes: ruedas, orejas) -> 3x3
  -> capa final: un numero por categoria; el mas alto es la respuesta.

Cada bloque tiene una convolucion (filtros de 3x3 que recorren la imagen
buscando un patron), max pooling (achica a la mitad quedandose con lo mas
fuerte) y dropout (apaga neuronas al azar al entrenar para que no
memorice los dibujos de entrenamiento).
"""

from pathlib import Path

import torch
from torch import nn

LADO = 28


def bloque(entrada, salida, dropout):
    capas = [
        nn.Conv2d(entrada, salida, 3, padding=1),
        nn.MaxPool2d(2),  # va antes de normalizar: mismo resultado y 4 veces menos cuentas
        nn.BatchNorm2d(salida),
        nn.ReLU(),
    ]
    if dropout:
        capas.append(nn.Dropout(dropout))
    return nn.Sequential(*capas)


class RedDibujos(nn.Module):
    def __init__(self, cantidad_categorias):
        super().__init__()
        self.convoluciones = nn.Sequential(
            bloque(1, 32, 0),      # 28 -> 14
            bloque(32, 64, 0.2),   # 14 -> 7
            bloque(64, 128, 0.3),  # 7 -> 3
        )
        self.clasificador = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 3 * 3, 256),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(256, cantidad_categorias),
        )

    def forward(self, x):
        """x: tensor (cantidad, 1, 28, 28) con valores de 0 a 1. Devuelve un puntaje por categoria."""
        return self.clasificador(self.convoluciones(x))


def guardar(ruta, red, categorias, info=None):
    """Guarda los pesos de la red junto con sus categorias [(ingles, castellano), ...]."""
    torch.save({"pesos": red.state_dict(), "categorias": categorias, "info": info or {}}, ruta)


def cargar(ruta="modelo.pt"):
    """Devuelve (red lista para predecir, categorias, info)."""
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No esta {ruta}. Entrenalo primero con: python entrenar.py")
    datos = torch.load(ruta, map_location="cpu", weights_only=False)
    categorias = [tuple(c) for c in datos["categorias"]]
    red = RedDibujos(len(categorias))
    red.load_state_dict(datos["pesos"])
    red.eval()
    return red, categorias, datos.get("info", {})


@torch.no_grad()
def predecir(red, array_28x28):
    """Array uint8 de 28x28 -> lista de probabilidades (una por categoria, suman 1)."""
    x = torch.as_tensor(array_28x28, dtype=torch.float32).reshape(1, 1, LADO, LADO) / 255.0
    return torch.softmax(red(x), dim=1)[0].tolist()
