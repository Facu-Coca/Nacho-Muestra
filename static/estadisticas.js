// Pestaña "Estadísticas": pide GET /estadisticas cada vez que se abre y arma los números,
// lo que más confunde la IA y los aciertos por categoría.

function nuevo(etiqueta, clase, texto) {
  const e = document.createElement(etiqueta);
  if (clase) e.className = clase;
  if (texto !== undefined) e.textContent = texto;
  return e;
}

const porcentaje = (x) => Math.round(x * 100) + "%";

// verde si le va bien, amarillo regular, rojo mal (el número también se muestra, el color no es lo único)
function claseDeNivel(p) {
  if (p >= 0.85) return "nivel-bien";
  if (p >= 0.6) return "nivel-medio";
  return "nivel-mal";
}

function mostrarSoloStats(cual) {   // "vacio" | "error" | "contenido"
  ["vacio", "error", "contenido"].forEach((n) => {
    document.getElementById("stats-" + n).hidden = (n !== cual);
  });
}

function dibujarConfusiones(lista) {
  const ul = document.getElementById("stats-confusiones");
  ul.innerHTML = "";
  if (!lista || lista.length === 0) {
    ul.appendChild(nuevo("li", "stats-sin-datos", "La IA todavía no se confundió. ¡Probá dibujar raro!"));
    return;
  }
  lista.forEach((c) => {
    const li = nuevo("li", "confusion");
    li.append(
      nuevo("span", "confusion-pares", `${c.pedida} → ${c.creyo}`),
      nuevo("span", "confusion-veces", c.veces === 1 ? "1 vez" : `${c.veces} veces`)
    );
    li.title = `Pedía ${c.pedida} y la IA creyó ${c.creyo}`;
    ul.appendChild(li);
  });
}

function dibujarCategorias(porCategoria) {
  const cont = document.getElementById("stats-categorias");
  cont.innerHTML = "";
  // de mejor a peor; si empatan, la que más se jugó primero
  const filas = Object.entries(porCategoria || {}).sort(
    (a, b) => b[1].porcentaje - a[1].porcentaje || b[1].jugados - a[1].jugados
  );
  filas.forEach(([nombre, d]) => {
    const fila = nuevo("div", "cat-fila");
    const barra = nuevo("div", "cat-barra " + claseDeNivel(d.porcentaje));
    barra.style.width = Math.max(d.porcentaje * 100, 2) + "%";
    const fondo = nuevo("div", "cat-fondo");
    fondo.appendChild(barra);
    const detalle = nuevo("span", "cat-pct", `${porcentaje(d.porcentaje)}`);
    detalle.title = `${d.aciertos} de ${d.jugados}`;
    fila.append(nuevo("span", "cat-nombre", nombre), fondo, detalle);
    cont.appendChild(fila);
  });
}

async function actualizarEstadisticas() {
  let datos;
  try {
    const r = await fetch("/estadisticas");
    if (!r.ok) throw new Error("HTTP " + r.status);
    datos = await r.json();
  } catch (err) {
    mostrarSoloStats("error");
    return;
  }
  if (!datos.dibujos_jugados) {
    mostrarSoloStats("vacio");
    return;
  }
  document.getElementById("stats-jugados").textContent = datos.dibujos_jugados;
  document.getElementById("stats-porcentaje").textContent = porcentaje(datos.porcentaje_aciertos || 0);
  document.getElementById("stats-aciertos").textContent =
    `${datos.aciertos} de ${datos.dibujos_jugados}`;
  dibujarConfusiones(datos.mas_confundidas);
  dibujarCategorias(datos.por_categoria);
  mostrarSoloStats("contenido");
}