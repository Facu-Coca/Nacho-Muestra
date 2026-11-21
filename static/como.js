// Pestaña "Cómo funciona": muestra, con el último dibujo que vio la IA, el recorrido
// dibujo -> imagen de 28x28 -> red neuronal -> resultado.
// ultimoDibujo lo completa app.js cada vez que llega una predicción.

function actualizarComoFunciona() {
  const dibujo = document.getElementById("como-dibujo");
  const vista = document.getElementById("como-vista");
  const resultado = document.getElementById("como-resultado");
  const aviso = document.getElementById("como-aviso");

  if (!ultimoDibujo) {   // todavía no se dibujó nada
    dibujo.hidden = true;
    vista.hidden = true;
    resultado.innerHTML = '<span class="paso-vacio">?</span>';
    aviso.hidden = false;
    return;
  }

  dibujo.src = ultimoDibujo.imagen;
  dibujo.hidden = false;
  if (ultimoDibujo.vistaIA) {
    vista.src = ultimoDibujo.vistaIA;
    vista.hidden = false;
  }

  resultado.innerHTML = "";
  ultimoDibujo.top.forEach((op, i) => {
    const fila = document.createElement("div");
    fila.className = "resultado-fila" + (i === 0 ? " primera" : "");
    fila.textContent = `${op.categoria} ${Math.round(op.prob * 100)}%`;
    resultado.appendChild(fila);
  });
  aviso.hidden = true;
}