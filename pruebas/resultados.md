# Resultados de evaluación de modelos

Responsable: Ivo (rama `ivo/pruebas`).
Se completa cada vez que Facu sube un modelo nuevo, corriendo `pruebas/evaluar.py`.

**Metas**

| Medida | Meta |
| --- | --- |
| Aciertos con dibujos de prueba de Quick, Draw! | más de 90% |
| Aciertos con dibujos propios (hechos en la página) | más de 85% ← **condición para dar el OK** |
| Correcta entre las 3 primeras (top-3) | más de 95% |

---

## Tabla general

| Fecha | Versión del modelo | Dibujos por categoría usados para entrenar | % Quick, Draw! (top-1) | % Dibujos propios (top-1) | % Top-3 (propios) | Cantidad de dibujos propios evaluados | ¿OK? | Notas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aaaa-mm-dd | v0 (provisorio) | | | | | | No | |
| | | | | | | | | |

---

## Categorías que más falla (último modelo)

| Categoría | % aciertos | Se confunde más con | Ejemplos (archivos en `datos_muestra/`) | ¿Avisado a Facu y Vicente? |
| --- | --- | --- | --- | --- |
| | | | | |

---

## Pares que más se confunden (último modelo)

| Dibujo pedido | La IA dijo | Veces | Posible solución (reentrenar / cambiar categoría) |
| --- | --- | --- | --- |
| | | | |

---

## Cómo completar

1. Bajar el modelo nuevo de Facu (`git pull` en `ivo/pruebas` después de que Facu lo junte).
2. Correr `python pruebas/evaluar.py` con los dibujos de prueba de Quick, Draw! y con `datos_muestra/`.
3. Agregar una fila en la tabla general (no borrar las anteriores, así se ve la evolución).
4. Actualizar las dos tablas de abajo y avisar por el grupo las categorías que fallan, con ejemplos.
5. Marcar **OK** solo si dibujos propios supera 85%.
