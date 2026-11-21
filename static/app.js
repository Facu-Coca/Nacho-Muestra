// Lienzo de dibujo: funciona con mouse, dedo y lápiz (pointer events).
// Paso 1: dibujar y borrar. Paso 2: predicción en vivo (manda el lienzo a /predecir cada 500 ms).

const lienzo = document.getElementById("lienzo");
const ctx = lienzo.getContext("2d");
const botonBorrar = document.getElementById("borrar");

// El lienzo mide 600x600 por dentro y se muestra más chico o más grande con CSS.
// Con 9 px a 600 de ancho queda un trazo proporcional a "6 px en 400".
const GROSOR = 9;

let dibujando = false;
let ultimo = null;
let lienzoBloqueado = false;   // juego.js lo pone en true cuando se acaba el tiempo

function prepararPincel() {
  ctx.lineWidth = GROSOR;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.strokeStyle = "#000";   // trazo negro
  ctx.fillStyle = "#000";
}

function limpiar() {
  ctx.fillStyle = "#fff";     // fondo blanco
  ctx.fillRect(0, 0, lienzo.width, lienzo.height);
  prepararPincel();
  // Aviso para que otras partes (paso 3) sepan que el dibujo cambió
  lienzo.dispatchEvent(new CustomEvent("dibujo-borrado"));
}

// Convierte la posición del mouse/dedo a coordenadas internas del lienzo
function posicion(e) {
  const r = lienzo.getBoundingClientRect();
  return {
    x: (e.clientX - r.left) * (lienzo.width / r.width),
    y: (e.clientY - r.top) * (lienzo.height / r.height),
  };
}

function empezar(e) {
  if (lienzoBloqueado) return;
  if (e.pointerType === "mouse" && e.button !== 0) return; // solo botón izquierdo
  e.preventDefault();
  dibujando = true;
  lienzo.setPointerCapture(e.pointerId);
  ultimo = posicion(e);
  // un toque sin mover deja un punto
  ctx.beginPath();
  ctx.arc(ultimo.x, ultimo.y, GROSOR / 2, 0, Math.PI * 2);
  ctx.fill();
  lienzo.dispatchEvent(new CustomEvent("dibujo-cambio"));
}

function mover(e) {
  if (!dibujando || lienzoBloqueado) return;
  e.preventDefault();
  const p = posicion(e);
  ctx.beginPath();
  ctx.moveTo(ultimo.x, ultimo.y);
  ctx.lineTo(p.x, p.y);
  ctx.stroke();
  ultimo = p;
  lienzo.dispatchEvent(new CustomEvent("dibujo-cambio"));
}

function terminar() {
  dibujando = false;
  ultimo = null;
}

lienzo.addEventListener("pointerdown", empezar);
lienzo.addEventListener("pointermove", mover);
lienzo.addEventListener("pointerup", terminar);
lienzo.addEventListener("pointercancel", terminar);
botonBorrar.addEventListener("click", limpiar);

// ---------------------------------------------------------------
// PASO 2: predicción en vivo
// ---------------------------------------------------------------
const panelOpciones = document.getElementById("opciones");
const MEDIO_SEGUNDO = 500;

let ultimoDibujo = null;    // { imagen, vistaIA, top } del último dibujo que vio la IA (lo usa "Cómo funciona")
let hayCambio = false;      // true si se dibujó algo desde el último envío
let enviando = false;       // evita mandar un pedido nuevo si el anterior no volvió
let version = 0;            // sube cada vez que se borra: descarta respuestas viejas

function mostrarPista(texto) {
  panelOpciones.innerHTML = "";
  const p = document.createElement("p");
  p.className = "pista";
  p.textContent = texto;
  panelOpciones.appendChild(p);
}

// Dibuja las 3 barras. top = [{categoria, prob}, ...] (ya viene ordenado de mayor a menor)
function mostrarOpciones(top) {
  panelOpciones.innerHTML = "";
  top.forEach((op, i) => {
    const pct = Math.round(op.prob * 100);
    const fila = document.createElement("div");
    fila.className = "opcion" + (i === 0 ? " primera" : "");

    const nombre = document.createElement("span");
    nombre.className = "opcion-nombre";
    nombre.textContent = op.categoria;

    const pista = document.createElement("div");
    pista.className = "barra-fondo";
    const barra = document.createElement("div");
    barra.className = "barra";
    barra.style.width = Math.max(pct, 1) + "%";
    pista.appendChild(barra);

    const numero = document.createElement("span");
    numero.className = "opcion-pct";
    numero.textContent = pct + "%";

    fila.append(nombre, pista, numero);
    panelOpciones.appendChild(fila);
  });
}

async function predecir() {
  if (!hayCambio || enviando) return;
  hayCambio = false;
  enviando = true;
  const miVersion = version;
  try {
    const imagen = lienzo.toDataURL("image/png");
    const r = await fetch("/predecir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ imagen }),
    });
    const res = await r.json();
    if (miVersion !== version) return;           // se borró mientras esperábamos
    if (!r.ok || res.error) {
      mostrarPista("Uy, algo falló. Probá de nuevo.");
    } else if (res.vacio || !res.top || res.top.length === 0) {
      mostrarPista("Empezá a dibujar y la IA te va a ir diciendo qué ve.");
    } else {
      mostrarOpciones(res.top);
      ultimoDibujo = { imagen, vistaIA: res.vista_ia, top: res.top };
      // Aviso para que juego.js pueda ver si la IA acertó
      lienzo.dispatchEvent(new CustomEvent("prediccion", { detail: res }));
    }
  } catch (err) {
    if (miVersion === version) mostrarPista("No me puedo conectar con el servidor.");
  } finally {
    enviando = false;
  }
}

lienzo.addEventListener("dibujo-cambio", () => { hayCambio = true; });
lienzo.addEventListener("dibujo-borrado", () => {
  version++;
  hayCambio = false;
  mostrarPista("Empezá a dibujar y la IA te va a ir diciendo qué ve.");
});

setInterval(predecir, MEDIO_SEGUNDO);

limpiar();