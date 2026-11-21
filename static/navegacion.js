// Navegación: pestañas de arriba (Jugar / Cómo funciona / Estadísticas)
// y pantallas dentro de "Jugar" (inicio -> juego -> final).
// Todo vive en la misma página: solo se muestra u oculta con el atributo "hidden".

const PESTANAS = ["jugar", "como", "stats"];
const PANTALLAS = ["inicio", "juego", "final"];

function mostrarPestana(nombre) {
  // si se va de "Jugar" en medio de una ronda, la ronda se cancela
  if (nombre !== "jugar" && typeof cancelarRonda === "function") cancelarRonda();
  PESTANAS.forEach(n => {
    document.getElementById("pestana-" + n).hidden = (n !== nombre);
  });
  if (nombre === "como" && typeof actualizarComoFunciona === "function") actualizarComoFunciona();
  if (nombre === "stats" && typeof actualizarEstadisticas === "function") actualizarEstadisticas();
  document.querySelectorAll(".pestana").forEach(boton => {
    boton.classList.toggle("activa", boton.dataset.pestana === nombre);
  });
}

function mostrarPantalla(nombre) {
  PANTALLAS.forEach(n => {
    document.getElementById("pantalla-" + n).hidden = (n !== nombre);
  });
}

document.querySelectorAll(".pestana").forEach(boton => {
  boton.addEventListener("click", () => mostrarPestana(boton.dataset.pestana));
});

// El botón "Jugar" lo maneja juego.js