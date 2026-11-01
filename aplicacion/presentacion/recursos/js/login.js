"use strict";

function mostrarTiempoLogin(segundos) {
    const minutos = Math.floor(segundos / 60);
    const restoSegundos = segundos % 60;
    return `${String(minutos).padStart(2, "0")}:${String(restoSegundos).padStart(2, "0")}`;
}

function iniciarContadorLogin() {
    const contador = document.querySelector("#contador-login");
    const tiempo = document.querySelector("#tiempo-login");
    if (!contador || !tiempo) return;

    const segundosIniciales = Number(contador.dataset.segundosRestantes || 0);
    const finalBloqueo = Date.now() + segundosIniciales * 1000;
    let intervalo;

    function actualizarContador() {
        const segundos = Math.max(0, Math.ceil((finalBloqueo - Date.now()) / 1000));
        tiempo.textContent = mostrarTiempoLogin(segundos);

        if (segundos === 0) {
            window.clearInterval(intervalo);
            contador.textContent = "Ya puedes intentarlo nuevamente.";
            document.querySelectorAll(".formulario-login input, .formulario-login button").forEach((campo) => {
                campo.disabled = false;
            });
            document.querySelector(".formulario-login input")?.focus();
        }
    }

    actualizarContador();
    intervalo = window.setInterval(actualizarContador, 1000);
}

document.addEventListener("DOMContentLoaded", iniciarContadorLogin);
