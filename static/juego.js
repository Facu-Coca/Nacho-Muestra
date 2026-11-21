// Modo juego: una ronda de 6 dibujos, cada uno con una categoría al azar y 20 segundos.
// 2.2: consigna + cuenta regresiva.  2.3: acierto, puntos y avance automático.
// 2.4: guarda cada dibujo en /guardar.  2.5: pantalla final con los 6 dibujos.

const TOTAL_DIBUJOS = 6;
const SEGUNDOS_POR_DIBUJO = 20;
const SEGUNDOS_URGENTE = 5;          // de acá para abajo el reloj se pone rojo
const PAUSA_ENTRE_DIBUJOS_MS = 2500; // cuánto se ve el resultado antes de pasar al siguiente
const PROB_MINIMA = 0.6;             // la IA tiene que poner la correcta primera y con más de 60%.
                                     // Con 0 cortaba el dibujo a los 2 trazos; si sigue cortando muy pronto, subirlo.

// Para decir "¡Es un elefante!" / "¡Es una mariposa!". Si se cambian las categorías,
// agregar acá las que sean femeninas o plurales (las demás van con "un").
const FEMENINAS = ["mariposa", "serpiente", "araña", "bicicleta", "guitarra", "llave",
                   "silla", "manzana", "pizza", "casa", "flor", "tijera", "banana"];
const PLURALES = ["anteojos"];

const elContador = document.getElementById("contador-dibujos");
const elPedida = document.getElementById("categoria-pedida");
const elBarra = document.getElementById("reloj-barra");
const elSegundos = document.getElementById("reloj-segundos");
const elMensaje = document.getElementById("mensaje-ronda");
const elDetalle = document.getElementById("detalle-ronda");

let todasLasCategorias = null;   // la lista que devuelve GET /categorias
let ronda = null;                // { pedidas, indice, puntos, resultados }
let estado = "quieto";           // "dibujando" mientras corre el reloj, "terminado" cuando ya se resolvió
let temporizador = null;
let pausa = null;                // el setTimeout que pasa al siguiente dibujo
let finDelTiempo = 0;            // hora (en ms) en que se termina el dibujo actual
let ultimaOpcion = null;         // lo que la IA creía en la última predicción: {categoria, prob}

async function cargarCategorias() {
  if (todasLasCategorias) return;
  const r = await fetch("/categorias");
  if (!r.ok) throw new Error("No se pudo leer /categorias");
  todasLasCategorias = await r.json();
}

// Mezcla una lista al azar (Fisher-Yates) sin tocar la original
function mezclar(lista) {
  const copia = [...lista];
  for (let i = copia.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copia[i], copia[j]] = [copia[j], copia[i]];
  }
  return copia;
}

function fraseEs(nombre) {
  if (PLURALES.includes(nombre)) return `¡Son unos ${nombre}!`;
  return FEMENINAS.includes(nombre) ? `¡Es una ${nombre}!` : `¡Es un ${nombre}!`;
}

function mostrarContador() {
  elContador.textContent =
    `Dibujo ${ronda.indice + 1} de ${ronda.pedidas.length} · Puntos: ${ronda.puntos}`;
}

async function iniciarRonda() {
  try {
    await cargarCategorias();
  } catch (err) {
    alert("No me puedo conectar con el servidor. ¿Está corriendo python app.py?");
    return;
  }
  // 6 categorías distintas: dentro de una ronda no se repite ninguna
  ronda = {
    pedidas: mezclar(todasLasCategorias).slice(0, TOTAL_DIBUJOS),
    indice: 0,
    puntos: 0,
    resultados: [],   // uno por dibujo: { pedida, adivino, creyo, imagen, guardado }
  };
  mostrarPantalla("juego");
  empezarDibujo();
}

function empezarDibujo() {
  const pedida = ronda.pedidas[ronda.indice];
  elPedida.textContent = pedida;
  mostrarContador();
  elMensaje.hidden = true;
  elDetalle.hidden = true;

  estado = "dibujando";
  ultimaOpcion = null;
  lienzoBloqueado = false;
  limpiar();                        // lienzo en blanco (viene de app.js)

  finDelTiempo = Date.now() + SEGUNDOS_POR_DIBUJO * 1000;
  clearInterval(temporizador);
  temporizador = setInterval(actualizarReloj, 100);
  actualizarReloj();
}

function actualizarReloj() {
  const restante = Math.max(0, finDelTiempo - Date.now());
  const segundos = Math.ceil(restante / 1000);
  elSegundos.textContent = segundos;
  elBarra.style.width = (restante / (SEGUNDOS_POR_DIBUJO * 1000) * 100) + "%";
  const urgente = segundos <= SEGUNDOS_URGENTE;
  elBarra.classList.toggle("urgente", urgente);
  elSegundos.classList.toggle("urgente", urgente);
  if (restante === 0) terminarDibujo(false);
}

// Manda el dibujo terminado a POST /guardar (el servidor lo deja en datos_muestra/ para reentrenar).
// Corre "de fondo": si falla no se interrumpe el juego, solo se anota en resultado.guardado.
async function guardarDibujo(resultado) {
  try {
    const r = await fetch("/guardar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        imagen: resultado.imagen,
        categoria: resultado.pedida,    // en castellano, como la devuelve /categorias
        adivino: resultado.adivino,     // lo que vio la persona durante el juego
      }),
    });
    const res = await r.json();
    resultado.guardado = r.ok && res.guardado === true;   // false si el lienzo estaba vacío
    if (!resultado.guardado) console.warn("No se guardó el dibujo:", res.motivo || res.error);
  } catch (err) {
    resultado.guardado = false;
    console.warn("No se pudo guardar el dibujo:", err);
  }
}

// Cierra el dibujo actual. adivino = true si la IA lo acertó, false si se acabó el tiempo.
function terminarDibujo(adivino) {
  if (estado !== "dibujando") return;   // ya se resolvió (evita contar dos veces)
  estado = "terminado";
  clearInterval(temporizador);
  lienzoBloqueado = true;

  const pedida = ronda.pedidas[ronda.indice];
  const creyo = adivino ? pedida : (ultimaOpcion ? ultimaOpcion.categoria : null);
  const resultado = {
    pedida,
    adivino,
    creyo,
    imagen: lienzo.toDataURL("image/png"),
    guardado: null,   // se completa cuando responde /guardar
  };
  ronda.resultados.push(resultado);
  guardarDibujo(resultado);   // sin await: el juego sigue mientras se guarda
  if (adivino) ronda.puntos++;
  mostrarContador();

  elMensaje.textContent = adivino ? fraseEs(pedida) : "No lo adiviné";
  elMensaje.className = "mensaje-ronda " + (adivino ? "ok" : "mal");
  elMensaje.hidden = false;
  if (!adivino) {
    elDetalle.textContent = creyo ? `Yo pensaba que era: ${creyo}` : "No llegué a ver ningún dibujo";
    elDetalle.hidden = false;
  }

  const esElUltimo = ronda.indice === ronda.pedidas.length - 1;
  // Se ve un momento el resultado de este dibujo y después sigue (o va a la pantalla final)
  pausa = setTimeout(esElUltimo ? mostrarFinal : siguienteDibujo, PAUSA_ENTRE_DIBUJOS_MS);
}

// ---------------------------------------------------------------
// Pantalla final
// ---------------------------------------------------------------
function crear(etiqueta, clase, texto) {
  const e = document.createElement(etiqueta);
  if (clase) e.className = clase;
  if (texto !== undefined) e.textContent = texto;
  return e;
}

function fraseFinal(puntos, total) {
  if (puntos === total) return "¡Perfecto! La IA entendió todos tus dibujos.";
  if (puntos >= total * 2 / 3) return "¡Muy bien! La IA entendió casi todo.";
  if (puntos >= total / 3) return "¡No estuvo mal! ¿Probamos otra vez?";
  return "¡La IA la tuvo difícil! ¿Revancha?";
}

function mostrarFinal() {
  const total = ronda.resultados.length;
  document.getElementById("final-puntaje").textContent =
    `La IA adivinó ${ronda.puntos} de ${total}. ${fraseFinal(ronda.puntos, total)}`;

  const contenedor = document.getElementById("final-dibujos");
  contenedor.innerHTML = "";
  ronda.resultados.forEach((r) => {
    const tarjeta = crear("figure", "dibujo-final " + (r.adivino ? "ok" : "mal"));

    const img = crear("img");
    img.src = r.imagen;
    img.alt = "Dibujo de " + r.pedida;

    const pedida = crear("figcaption", "dibujo-pedida", (r.adivino ? "✔ " : "✘ ") + r.pedida);
    const creyo = crear("div", "dibujo-creyo",
      r.adivino ? "La IA lo adivinó"
                : (r.creyo ? "La IA creyó: " + r.creyo : "La IA no vio nada"));

    tarjeta.append(img, pedida, creyo);
    contenedor.appendChild(tarjeta);
  });
  mostrarPantalla("final");
}

function siguienteDibujo() {
  ronda.indice++;
  empezarDibujo();
}

function cancelarRonda() {
  clearInterval(temporizador);
  clearTimeout(pausa);
  estado = "quieto";
  lienzoBloqueado = false;
  ronda = null;
  mostrarPantalla("inicio");
}

// app.js avisa cada vez que llega una predicción de la IA
lienzo.addEventListener("prediccion", (e) => {
  if (!ronda || estado !== "dibujando") return;
  const top = e.detail.top;
  if (!top || top.length === 0) return;
  ultimaOpcion = top[0];
  if (top[0].categoria === ronda.pedidas[ronda.indice] && top[0].prob >= PROB_MINIMA) {
    terminarDibujo(true);
  }
});

document.getElementById("jugar-de-nuevo").addEventListener("click", iniciarRonda);
document.getElementById("jugar").addEventListener("click", iniciarRonda);