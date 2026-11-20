// Navegación: pestañas de arriba (Jugar / Cómo funciona / Estadísticas)
// y pantallas dentro de "Jugar" (inicio -> juego -> final).
// Todo vive en la misma página: solo se muestra u oculta con el atributo "hidden".

const PESTANAS = ["jugar", "como", "stats"];
const PANTALLAS = ["inicio", "juego"];   // el 2.5 le suma "final"

function mostrarPestana(nombre) {
  PESTANAS.forEach(n => {
    document.getElementById("pestana-" + n).hidden = (n !== nombre);
  });
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

document.getElementById("jugar").addEventListener("click", () => {
  mostrarPantalla("juego");
  limpiar();   // lienzo en blanco (la función viene de app.js)
});