# Adiviná el Dibujo con IA

Juego de navegador: la página te pide que dibujes algo y una red neuronal entrenada
por nosotros con los dibujos de [Quick, Draw!](https://quickdraw.withgoogle.com/data)
intenta adivinar qué es mientras dibujás. Funciona sin internet.

## Correrlo

Necesita Python 3.11 o superior.

```
pip install flask numpy pillow
pip install torch --index-url https://download.pytorch.org/whl/cpu
python app.py
```

Abrir http://127.0.0.1:5000. `modelo.pt` ya viene entrenado en el repo, así que para
jugar no hace falta descargar nada más.

## Entrenar de nuevo

```
python descargar.py           # baja los dibujos de categorias.txt a datos/ (~2,9 GB, no se suben al repo)
python entrenar.py            # entrenamiento completo, guarda modelo.pt
python entrenar.py --rapido   # modelo provisorio en un par de minutos
python reentrenar.py          # suma los dibujos guardados en la muestra (datos_muestra/)
```

En una notebook sin placa de video, el entrenamiento completo tarda alrededor de 1 hora
(unos 10 minutos por época). Si la compu tiene placa NVIDIA, `entrenar.py` la usa sola:
instalar torch con CUDA (`pip install torch --index-url https://download.pytorch.org/whl/cu128`)
y tarda unos minutos. Al empezar dice con qué está entrenando.

Para cambiar categorías: editar `categorias.txt` (nombre en inglés exacto de
[la lista de Quick, Draw!](https://github.com/googlecreativelab/quickdraw-dataset/blob/master/categories.txt),
coma, nombre en castellano), correr `descargar.py` y `entrenar.py`.

## Archivos

| Archivo | Qué hace |
| --- | --- |
| `app.py` | Servidor Flask con las rutas del contrato |
| `modelo.py` | La red neuronal (CNN de 3 bloques: 32, 64 y 128 filtros) |
| `entrenar.py` | Entrena y muestra aciertos por categoría y qué confunde |
| `reentrenar.py` | Reentrena sumando los dibujos de la muestra |
| `procesamiento.py` | Pasa el dibujo del lienzo a 28×28 como los de Quick, Draw! |
| `descargar.py` | Baja los `.npy` de Quick, Draw! |
| `categorias.txt` | Las 25 categorías |
| `templates/`, `static/` | La página (Sebas). El `index.html` actual es una página de prueba |
| `pruebas/` | Dibujos de prueba y script de evaluación (Ivo) |
| `docs/` | Textos, cartel y guion (Vicente) |

## Contrato entre la página y el servidor

Todas las imágenes van como texto base64 del PNG del lienzo, tal cual lo da
`lienzo.toDataURL("image/png")` (con o sin el prefijo `data:image/png;base64,`).
El lienzo puede ser de cualquier tamaño; conviene fondo blanco y trazo negro de unos 6 px.

**`GET /categorias`** → lista de nombres en castellano.
```json
["gato", "elefante", "pez", "..."]
```

**`POST /predecir`** — mandarlo cada medio segundo mientras se dibuja.
```json
{"imagen": "data:image/png;base64,..."}
```
Respuesta:
```json
{
  "top": [{"categoria": "elefante", "prob": 0.82}, {"categoria": "gato", "prob": 0.09}, {"categoria": "pez", "prob": 0.04}],
  "vista_ia": "data:image/png;base64,...",
  "vacio": false
}
```
`vista_ia` es la imagen de 28×28 que ve la IA: mostrarla agrandada con
`image-rendering: pixelated`. Si el lienzo está vacío vuelve `{"top": [], "vista_ia": null, "vacio": true}`.

**`POST /guardar`** — al terminar cada dibujo.
```json
{"imagen": "data:image/png;base64,...", "categoria": "elefante", "adivino": true}
```
`categoria` es la que se pidió (tiene que ser una de `/categorias`). `adivino` es
opcional: si la IA acertó en algún momento del dibujo, mandarlo en `true`; si no se
manda, se decide con el dibujo final. Respuesta: `{"guardado": true, "creyo": "elefante", "adivino": true}`.
Los dibujos quedan en `datos_muestra/<categoria en inglés>/` y en `datos_muestra/registro.csv`.

**`GET /estadisticas`**
```json
{
  "dibujos_jugados": 120, "aciertos": 103, "porcentaje_aciertos": 0.8583,
  "por_categoria": {"gato": {"jugados": 6, "aciertos": 5, "porcentaje": 0.8333}},
  "mas_confundidas": [{"pedida": "sol", "creyo": "flor", "veces": 4}],
  "modelo": {"fecha": "2026-11-16T10:00", "provisorio": false, "aciertos_prueba_quickdraw": 0.93, "top3_prueba_quickdraw": 0.98}
}
```

Los errores vuelven con código 400 y `{"error": "explicación"}`.
