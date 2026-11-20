"""Reentrena el modelo sumando los dibujos que la gente hizo en la muestra (datos_muestra/).

Arranca desde el modelo actual (no de cero), asi tarda menos. Antes de pisar
modelo.pt guarda una copia en modelo_anterior.pt por si el nuevo anda peor.

Uso:  python reentrenar.py            (por defecto 3 epocas)
      python reentrenar.py --epocas 5
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).parent


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--epocas", type=int, default=3)
    args = parser.parse_args()

    actual = RAIZ / "modelo.pt"
    if not actual.exists():
        sys.exit("No hay modelo.pt para reentrenar. Primero: python entrenar.py")
    if not any((RAIZ / "datos_muestra").glob("*/*.png")):
        sys.exit("No hay dibujos en datos_muestra/ todavia. Juga unas rondas primero.")

    shutil.copy(actual, RAIZ / "modelo_anterior.pt")
    print("Copia de seguridad: modelo_anterior.pt")
    comando = [sys.executable, str(RAIZ / "entrenar.py"), "--con-muestra", "--desde", "modelo_anterior.pt",
               "--epocas", str(args.epocas), "--aprendizaje", "0.001", "--salida", "modelo.pt"]
    sys.exit(subprocess.call(comando, cwd=RAIZ))


if __name__ == "__main__":
    main()
