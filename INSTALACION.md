# Instalación de Adiviná el Dibujo

Instructivo para correr el juego en una compu nueva, paso a paso.

- **Windows (compus del labo / muestra):** sección principal. Probada en una compu del labo (PC-12):
  **Windows 8.1**, Python 3.11.4, Git 2.55.
- **Linux Mint:** probado (Python 3.12.3), está al final.

> **Importante para la muestra:** el juego funciona sin internet, pero **la instalación necesita internet**
> (bajar Python, Git, las librerías y el repo). Hacer todo esto antes del día de la muestra, en la compu
> que se va a usar, y probar que anda con el wifi apagado.

---

## Cómo son las compus del labo

- Windows 8.1, viejas.
- **Python 3.11.4 y Git ya vienen instalados** (pasos 1 y 2 se saltean).
- Se puede instalar programas sin contraseña de administrador.
- Hay internet y se pudo bajar PyTorch sin bloqueos.
- **Están freezadas** (ver abajo).

---

## ⚠️ Las compus del labo están "freezadas"

Cada vez que se apagan **vuelven al estado anterior**: se borra el repo, el entorno virtual,
lo instalado y **los dibujos guardados** en `datos_muestra/`.

- **El día de la muestra** hay que instalar todo de nuevo antes de empezar. Calcular el tiempo, sobre todo
  para bajar PyTorch, o llevar los paquetes en pendrive (ver "Si en el labo no se puede bajar PyTorch").
- **No apagar la compu durante la muestra.**
- **Antes de apagarla, copiar `datos_muestra/` a un pendrive.** Son los dibujos de los visitantes que se usan
  para reentrenar. Si no se copian, se pierden.
- Otra opción: pedirle al encargado del labo que descongele una compu para la muestra.

---

## Instalación en Windows

Todo esto se hace **una sola vez**.

### 1. Instalar Python

Bajar Python 3.11 o superior de https://www.python.org/downloads/ y abrir el instalador.

- En la primera pantalla **tildar "Add python.exe to PATH"** antes de tocar "Install Now".
  Si no se tilda, después PowerShell no encuentra `python`.

Para comprobarlo, abrir **PowerShell** (menú Inicio → escribir "PowerShell") y correr:

```powershell
python --version
```

Tiene que decir `Python 3.11` o mayor. Si abre la Microsoft Store en vez de mostrar la versión,
Python no quedó en el PATH: reinstalar tildando la opción.

### 2. Instalar Git

Bajar de https://git-scm.com/download/win e instalar con las opciones que vienen por defecto.
Cerrar y volver a abrir PowerShell después de instalarlo.

### 3. Bajar el repo

```powershell
cd $HOME/Documents
git clone https://github.com/Facu-Coca/Nacho-Muestra.git
cd Nacho-Muestra
```

### 4. Crear y activar el entorno virtual

El entorno virtual es una carpeta `.venv` dentro del repo con las librerías del proyecto.
Ya está en `.gitignore`, así que no se sube.

```powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
```

- Crear el entorno **no muestra ningún mensaje** cuando sale bien.
- Al activarlo, Windows muestra un error en rojo: **la ejecución de scripts está deshabilitada**
  (pasó en las compus del labo). Habilitarlos **solo para esa ventana**, sin cambiar la configuración
  de la compu, y volver a activar:
  ```powershell
  Set-ExecutionPolicy -Scope Process Bypass
  .venv/Scripts/Activate.ps1
  ```
  Si pregunta si querés cambiar la directiva, responder que sí. Hay que repetirlo en cada PowerShell nueva.
- Para saber si quedó activo, fijarse que aparezca `(.venv)` al principio de la línea.

### 5. Instalar las librerías

Con el entorno activo, **primero actualizar pip**. El pip que trae Python 3.11.4 (versión 23.1) falla al
instalar PyTorch con el error `Could not find a version that satisfies the requirement flit_core`.

```powershell
python -m pip install --upgrade pip
pip install flask numpy pillow
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

PyTorch pesa unos 200 MB y puede tardar varios minutos.

### 6. Instalar Visual C++ (compus del labo)

Sin esto, `python app.py` falla con:
`OSError: [WinError 126] No se puede encontrar el módulo especificado. Error loading ...torch\lib\shm.dll`

1. Bajar el instalador oficial de Microsoft: https://aka.ms/vs/17/release/vc_redist.x64.exe
2. Abrirlo, aceptar la licencia e **Instalar**. No pidió contraseña de administrador.
3. Al final pide **reiniciar: NO reiniciar** (la compu está freezada y se borraría todo).
   Cerrar el instalador y seguir: funciona igual sin reiniciar.

### Si en el labo no se puede bajar PyTorch

En una compu con internet y **Windows con la misma versión de Python**, bajar los archivos sin instalarlos:

```powershell
pip download flask numpy pillow -d paquetes
pip download torch --index-url https://download.pytorch.org/whl/cpu -d paquetes
```

Copiar la carpeta `paquetes` a un pendrive y en el labo, con el entorno activo:

```powershell
pip install --no-index --find-links paquetes flask numpy pillow torch
```

---

## Correr el juego (cada vez)

Cada vez que se abre una PowerShell nueva hay que hacer estos 3 pasos.
**No hace falta volver a instalar nada:** lo instalado queda guardado en `.venv`.

```powershell
cd $HOME/Documents/Nacho-Muestra
Set-ExecutionPolicy -Scope Process Bypass
.venv/Scripts/Activate.ps1
python app.py
```

Después abrir en el navegador: **http://127.0.0.1:5000**

Para cortar el servidor: `Ctrl+C` en PowerShell.

Si Windows muestra un aviso del **Firewall** al correr `python app.py`, se puede cancelar:
el juego se usa en la misma compu y no necesita abrir la red.

### Prueba final para la muestra

- [x] Cortar el wifi / desenchufar el cable.
- [x] Correr los 3 pasos de arriba.
- [x] Dibujar algunas cosas y ver que adivine. **Probado en el labo (PC-12): anda sin internet.**

---

## Instalación en Linux (Mint / Ubuntu) — probada

### 1. Instalar pip y venv

En Linux Mint, Python viene instalado pero **`pip` no** (`No se ha encontrado la orden «pip»`).

```bash
sudo apt install python3-pip python3-venv
```

- Pide la contraseña de la compu. Mientras la escribís no se ve nada, es normal.
- Cuando pregunta `¿Desea continuar? [S/n]`, **apretá solo Enter**. Si escribís `s` puede responder
  `Anulado.` y no instala nada. Si pasa, usar `sudo apt install -y python3-pip python3-venv`.

### 2. Bajar el repo, crear el entorno e instalar

```bash
cd ~/Documentos
git clone https://github.com/Facu-Coca/Nacho-Muestra.git
cd Nacho-Muestra
python3 -m venv .venv
source .venv/bin/activate
pip install flask numpy pillow
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

- En Mint **no se puede** usar `pip install` directo en el sistema (error `externally-managed-environment`): por eso el entorno virtual.
- Si la terminal usa *fish*: `source .venv/bin/activate.fish`.

### 3. Correr el juego (cada vez)

```bash
cd ~/Documentos/Nacho-Muestra
source .venv/bin/activate
python app.py
```

En la terminal de Linux **`Ctrl+V` no pega**: usar `Ctrl+Shift+V` o clic derecho → Pegar.

---

## Problemas encontrados

| Problema | Dónde | Solución |
| --- | --- | --- |
| `pip` no está instalado | Linux Mint | `sudo apt install python3-pip python3-venv` |
| `apt` responde `Anulado.` al escribir `s` | Linux Mint en castellano | Apretar solo Enter, o usar `-y` |
| `python3 -m venv` no muestra nada | Linux | Es normal; después hay que activarlo |
| Al cerrar la terminal "se pierde todo" | Todas | No se pierde: solo repetir `cd`, activar y `python app.py` |
| `git clone` pide usuario de GitHub | Windows (labo) | La dirección tenía un error de tipeo: con un repo que no existe, GitHub pide login. Copiarla exacta |
| El README dice `pip install` directo | README | En Linux Mint hace falta el entorno virtual |
| Python y Git ya estaban instalados (Python 3.11.4, Git 2.55) | Windows (labo) | Saltear los pasos 1 y 2 |
| `Activate.ps1`: "la ejecución de scripts está deshabilitada" | Windows (labo) | `Set-ExecutionPolicy -Scope Process Bypass` (solo esa ventana) |
| La compu vuelve al estado anterior al apagarse (freezada) | Windows (labo) | Instalar el mismo día y copiar `datos_muestra/` antes de apagar |
| No se encuentra la barra invertida `\` en el teclado | Windows (labo) | PowerShell acepta `/`: `.venv/Scripts/Activate.ps1` |
| El comando de torch quedó partido en dos líneas | Windows (labo) | Escribirlo entero en una sola línea antes de Enter |
| `(.venv)` no aparece y `pip` instala en `...\Python311\...` | Windows (labo) | El entorno no estaba activo: repetir `Set-ExecutionPolicy` y `Activate.ps1` |
| Torch falla: `No matching distribution found for flit_core` | Windows (labo), pip 23.1 | Actualizar pip antes: `python -m pip install --upgrade pip` |
| `python app.py`: `OSError: [WinError 126] ... torch\lib\shm.dll` | Windows (labo, Win 8.1) | Instalar Visual C++ Redistributable (paso 6) **sin reiniciar**. Con eso anda en Windows 8.1 |
| *(completar en el labo)* | Windows | |
