"use strict";

const estado = {
    filiales: [],
    tasas: [],
    productos: [],
    inventario: [],
    ventas: [],
    reporte: null,
};

let temporizadorNotificacion;

// ============================================================
// BLOQUE: COMUNICACION CON EL BACKEND FLASK
// Centraliza las solicitudes para que todos los modulos interpreten
// de la misma forma los mensajes correctos y los errores de la API.
// ============================================================
async function solicitar(ruta, opciones = {}) {
    const configuracion = { ...opciones };
    configuracion.headers = { "Content-Type": "application/json", ...(opciones.headers || {}) };
    const respuesta = await fetch(ruta, configuracion);
    const cuerpo = await respuesta.json().catch(() => ({ mensaje: "Respuesta no válida del servidor." }));
    if (!respuesta.ok || cuerpo.exito === false) {
        throw new Error(cuerpo.mensaje || "No fue posible completar la operación.");
    }
    return cuerpo;
}

function datosFormulario(formulario) {
    return Object.fromEntries(new FormData(formulario).entries());
}

function textoSeguro(valor) {
    return String(valor ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function mostrarNotificacion(mensaje, esError = false) {
    const notificacion = document.querySelector("#notificacion");
    clearTimeout(temporizadorNotificacion);
    notificacion.textContent = mensaje;
    notificacion.classList.toggle("error", esError);
    notificacion.classList.add("visible");
    temporizadorNotificacion = setTimeout(() => notificacion.classList.remove("visible"), 4200);
}

function bloquearBoton(formulario, bloquear) {
    const boton = formulario.querySelector("button[type='submit']");
    if (!boton) return;
    boton.disabled = bloquear;
    boton.dataset.textoOriginal ||= boton.textContent;
    boton.textContent = bloquear ? "Procesando..." : boton.dataset.textoOriginal;
}

function hoyISO() {
    const ahora = new Date();
    const diferencia = ahora.getTimezoneOffset() * 60000;
    return new Date(ahora.getTime() - diferencia).toISOString().slice(0, 10);
}

function fechaHoraLocal() {
    const ahora = new Date();
    const diferencia = ahora.getTimezoneOffset() * 60000;
    return new Date(ahora.getTime() - diferencia).toISOString().slice(0, 16);
}

function inicioMesISO() {
    const hoy = new Date();
    hoy.setDate(1);
    const diferencia = hoy.getTimezoneOffset() * 60000;
    return new Date(hoy.getTime() - diferencia).toISOString().slice(0, 10);
}

function formatearFecha(valor, incluirHora = false) {
    if (!valor) return "—";
    const fecha = new Date(incluirHora ? valor : `${valor}T00:00:00`);
    return new Intl.DateTimeFormat("es-PE", incluirHora
        ? { dateStyle: "short", timeStyle: "short" }
        : { dateStyle: "medium" }).format(fecha);
}

function formatearImporte(valor, codigo = "EUR") {
    const numero = Number(valor);
    if (!Number.isFinite(numero)) return "—";
    try {
        return new Intl.NumberFormat("es-PE", { style: "currency", currency: codigo }).format(numero);
    } catch (_error) {
        return `${numero.toFixed(2)} ${codigo}`;
    }
}

function obtenerFilial(idFilial) {
    return estado.filiales.find((filial) => Number(filial.id_filial) === Number(idFilial));
}

function obtenerProducto(idProducto) {
    return estado.productos.find((producto) => Number(producto.id_producto) === Number(idProducto));
}

// ============================================================
// BLOQUE: NAVEGACION RESPONSIVA ENTRE MODULOS
// Cambia la seccion visible sin recargar la pagina y mantiene el menu
// lateral utilizable tanto en escritorio como en dispositivos moviles.
// ============================================================
function mostrarSeccion(nombre) {
    document.querySelectorAll(".seccion-modulo").forEach((seccion) => {
        seccion.classList.toggle("activa", seccion.id === `seccion-${nombre}`);
    });
    document.querySelectorAll(".enlace-navegacion").forEach((enlace) => {
        enlace.classList.toggle("activo", enlace.dataset.seccion === nombre);
    });
    const seccion = document.querySelector(`#seccion-${nombre}`);
    document.querySelector("#titulo-seccion").textContent = seccion?.dataset.titulo || "SERF";
    cerrarMenuMovil();
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function cerrarMenuMovil() {
    document.querySelector("#barra-lateral").classList.remove("abierta");
    document.querySelector("#fondo-menu").classList.remove("visible");
    document.querySelector("#boton-menu").setAttribute("aria-expanded", "false");
}

function prepararNavegacion() {
    document.querySelectorAll("[data-seccion]").forEach((boton) => {
        boton.addEventListener("click", () => mostrarSeccion(boton.dataset.seccion));
    });
    document.querySelectorAll("[data-ir-a]").forEach((boton) => {
        boton.addEventListener("click", () => mostrarSeccion(boton.dataset.irA));
    });
    document.querySelectorAll("[data-alternar]").forEach((boton) => {
        boton.addEventListener("click", () => {
            document.querySelector(`#${boton.dataset.alternar}`).classList.toggle("oculto");
        });
    });
    document.querySelector("#boton-menu").addEventListener("click", () => {
        const barra = document.querySelector("#barra-lateral");
        const abierta = barra.classList.toggle("abierta");
        document.querySelector("#fondo-menu").classList.toggle("visible", abierta);
        document.querySelector("#boton-menu").setAttribute("aria-expanded", String(abierta));
    });
    document.querySelector("#fondo-menu").addEventListener("click", cerrarMenuMovil);
}

function llenarSelectoresFiliales() {
    document.querySelectorAll(".selector-filiales").forEach((selector) => {
        const valorActual = selector.value;
        const primeraOpcion = selector.options[0]?.outerHTML || '<option value="">Seleccionar filial</option>';
        selector.innerHTML = primeraOpcion + estado.filiales
            .filter((filial) => filial.activa)
            .map((filial) => `<option value="${filial.id_filial}">${textoSeguro(filial.codigo)} · ${textoSeguro(filial.nombre)}</option>`)
            .join("");
        if ([...selector.options].some((opcion) => opcion.value === valorActual)) selector.value = valorActual;
    });
}

function mostrarIndicadores() {
    document.querySelector("#total-filiales").textContent = estado.filiales.filter((filial) => filial.activa).length;
    document.querySelector("#total-productos").textContent = estado.productos.filter((producto) => producto.activo).length;
    document.querySelector("#total-tasas").textContent = estado.tasas.filter((tasa) => tasa.activa).length;
    document.querySelector("#total-ventas").textContent = estado.ventas.length;
}

function mostrarFiliales() {
    const cuerpo = document.querySelector("#tabla-filiales");
    cuerpo.innerHTML = estado.filiales.map((filial) => `
        <tr>
            <td data-label="Código"><strong>${textoSeguro(filial.codigo)}</strong></td>
            <td data-label="Filial">${textoSeguro(filial.nombre)}</td>
            <td data-label="Ubicación">${textoSeguro(filial.ciudad)}, ${textoSeguro(filial.pais)}</td>
            <td data-label="Moneda"><span class="insignia insignia-neutra">${textoSeguro(filial.codigo_divisa)}</span></td>
        </tr>`).join("");
    document.querySelector("#vacio-filiales").classList.toggle("visible", estado.filiales.length === 0);
    llenarSelectoresFiliales();
}

function mostrarTasas() {
    document.querySelector("#tabla-tasas").innerHTML = estado.tasas.slice(0, 8).map((tasa) => `
        <tr>
            <td data-label="Divisa"><strong>${textoSeguro(tasa.codigo_divisa_origen)}/EUR</strong></td>
            <td data-label="Tasa EUR">${textoSeguro(tasa.tasa)}</td>
            <td data-label="Vigencia">${formatearFecha(tasa.fecha_vigencia)}</td>
            <td data-label="Estado"><span class="insignia ${tasa.activa ? "insignia-correcta" : "insignia-neutra"}">${tasa.activa ? "Activa" : "Histórica"}</span></td>
        </tr>`).join("");
    document.querySelector("#vacio-tasas").classList.toggle("visible", estado.tasas.length === 0);
}

function mostrarProductos(filtro = "") {
    const texto = filtro.trim().toLowerCase();
    const productos = estado.productos.filter((producto) =>
        !texto || producto.sku.toLowerCase().includes(texto) || producto.nombre.toLowerCase().includes(texto));
    document.querySelector("#tabla-productos").innerHTML = productos.map((producto) => `
        <tr>
            <td data-label="SKU"><strong>${textoSeguro(producto.sku)}</strong></td>
            <td data-label="Producto"><span class="dato-principal"><strong>${textoSeguro(producto.nombre)}</strong><small>${textoSeguro(producto.proveedor)}</small></span></td>
            <td data-label="Categoría">${textoSeguro(producto.categoria)}</td>
            <td data-label="Costo CNY">${formatearImporte(producto.costo_unitario_cny, "CNY")}</td>
            <td data-label="Costo EUR">${formatearImporte(producto.costo_unitario_eur, "EUR")}</td>
            <td data-label="Importación">${formatearFecha(producto.fecha_importacion)}</td>
        </tr>`).join("");
    document.querySelector("#vacio-productos").classList.toggle("visible", productos.length === 0);
}

function llenarProductosInventario() {
    const selector = document.querySelector("#producto-reposicion");
    const valorActual = selector.value;
    selector.innerHTML = '<option value="">Seleccionar producto</option>' + estado.inventario.map((item) => {
        const producto = obtenerProducto(item.id_producto);
        return `<option value="${item.id_producto}">${textoSeguro(producto?.sku || "")} · ${textoSeguro(producto?.nombre || "Producto")}</option>`;
    }).join("");
    if ([...selector.options].some((opcion) => opcion.value === valorActual)) selector.value = valorActual;
}

function mostrarInventario() {
    const idFilial = document.querySelector("#filtro-filial-inventario").value;
    const filial = obtenerFilial(idFilial);
    document.querySelector("#subtitulo-inventario").textContent = filial
        ? `${filial.nombre} · precios expresados en ${filial.codigo_divisa}`
        : "Selecciona una filial para consultar.";
    document.querySelector("#tabla-inventario").innerHTML = estado.inventario.map((item) => {
        const producto = obtenerProducto(item.id_producto);
        const stockBajo = Number(item.stock_disponible) <= 5;
        return `
            <tr>
                <td data-label="SKU"><strong>${textoSeguro(producto?.sku || item.id_producto)}</strong></td>
                <td data-label="Producto">${textoSeguro(producto?.nombre || "Producto")}</td>
                <td data-label="Stock"><strong>${item.stock_disponible}</strong></td>
                <td data-label="Precio local">${formatearImporte(item.precio_venta_local, filial?.codigo_divisa || "EUR")}</td>
                <td data-label="Estado"><span class="insignia ${stockBajo ? "insignia-alerta" : "insignia-correcta"}">${stockBajo ? "Stock bajo" : "Disponible"}</span></td>
            </tr>`;
    }).join("");
    document.querySelector("#vacio-inventario").classList.toggle("visible", estado.inventario.length === 0);
    llenarProductosInventario();
}

function mostrarVentas() {
    document.querySelector("#tabla-ventas").innerHTML = estado.ventas.map((venta) => {
        const filial = obtenerFilial(venta.id_filial);
        return `
            <tr>
                <td data-label="Factura"><strong>${textoSeguro(venta.numero_factura)}</strong></td>
                <td data-label="Fecha">${formatearFecha(venta.fecha_venta, true)}</td>
                <td data-label="Filial">${textoSeguro(filial?.nombre || venta.id_filial)}</td>
                <td data-label="Cliente">${textoSeguro(venta.cliente)}</td>
                <td data-label="Total local">${formatearImporte(venta.total_local, venta.codigo_divisa)}</td>
                <td data-label="Total EUR"><strong>${formatearImporte(venta.total_eur, "EUR")}</strong></td>
            </tr>`;
    }).join("");
    document.querySelector("#vacio-ventas").classList.toggle("visible", estado.ventas.length === 0);
    mostrarIndicadores();
}

async function cargarInventario(idFilial) {
    if (!idFilial) {
        estado.inventario = [];
        mostrarInventario();
        return;
    }
    const respuesta = await solicitar(`/api/inventario?id_filial=${encodeURIComponent(idFilial)}`);
    estado.inventario = respuesta.datos;
    document.querySelector("#filtro-filial-inventario").value = idFilial;
    mostrarInventario();
}

async function cargarVentas() {
    const desde = document.querySelector("#ventas-desde").value;
    const hasta = document.querySelector("#ventas-hasta").value;
    const filial = document.querySelector("#ventas-filial").value;
    const parametros = new URLSearchParams({ fecha_inicio: desde, fecha_fin: hasta });
    if (filial) parametros.set("id_filial", filial);
    const respuesta = await solicitar(`/api/ventas?${parametros}`);
    estado.ventas = respuesta.datos;
    mostrarVentas();
}

async function actualizarDatosGenerales() {
    const [filiales, tasas, productos] = await Promise.all([
        solicitar("/api/configuracion/filiales"),
        solicitar("/api/configuracion/tipos-cambio"),
        solicitar("/api/productos"),
    ]);
    estado.filiales = filiales.datos;
    estado.tasas = tasas.datos;
    estado.productos = productos.datos;
    mostrarFiliales();
    mostrarTasas();
    mostrarProductos(document.querySelector("#buscar-producto").value);
    mostrarIndicadores();
}

async function prepararVentaPorFilial(idFilial) {
    const selector = document.querySelector("#producto-venta");
    document.querySelector("#detalle-stock").textContent = "Consultando productos disponibles...";
    if (!idFilial) {
        selector.innerHTML = '<option value="">Seleccionar una filial primero</option>';
        document.querySelector("#detalle-stock").textContent = "Selecciona un producto para consultar su disponibilidad.";
        return;
    }
    const respuesta = await solicitar(`/api/inventario?id_filial=${encodeURIComponent(idFilial)}`);
    const disponibles = respuesta.datos.filter((item) => Number(item.stock_disponible) > 0);
    selector.innerHTML = '<option value="">Seleccionar producto</option>' + disponibles.map((item) => {
        const producto = obtenerProducto(item.id_producto);
        return `<option value="${item.id_producto}" data-stock="${item.stock_disponible}" data-precio="${item.precio_venta_local}">${textoSeguro(producto?.sku || "")} · ${textoSeguro(producto?.nombre || "Producto")}</option>`;
    }).join("");
    document.querySelector("#detalle-stock").textContent = disponibles.length
        ? "Selecciona un producto para consultar su disponibilidad."
        : "La filial no tiene productos con stock disponible.";
}

function actualizarDetalleStock() {
    const selector = document.querySelector("#producto-venta");
    const opcion = selector.selectedOptions[0];
    const filial = obtenerFilial(document.querySelector("#filial-venta").value);
    document.querySelector("#detalle-stock").textContent = opcion?.value
        ? `Disponible: ${opcion.dataset.stock} unidades · Precio: ${formatearImporte(opcion.dataset.precio, filial?.codigo_divisa || "EUR")}`
        : "Selecciona un producto para consultar su disponibilidad.";
}

function mostrarResumenVenta(venta) {
    const filial = obtenerFilial(venta.id_filial);
    document.querySelector("#resumen-ultima-venta").innerHTML = `
        <p class="etiqueta">Operación confirmada</p>
        <h3>${textoSeguro(venta.numero_factura)}</h3>
        <div class="datos-venta">
            <div><span>Filial</span><strong>${textoSeguro(filial?.nombre || venta.id_filial)}</strong></div>
            <div><span>Cliente</span><strong>${textoSeguro(venta.cliente)}</strong></div>
            <div><span>Total local</span><strong>${formatearImporte(venta.total_local, venta.codigo_divisa)}</strong></div>
            <div class="total-destacado"><span>Total corporativo</span><strong>${formatearImporte(venta.total_eur, "EUR")}</strong></div>
        </div>`;
}

function actualizarCamposPeriodoReporte() {
    const tipo = document.querySelector("#tipo-reporte").value;
    document.querySelector("#campo-mes-reporte").classList.toggle("oculto", tipo !== "mensual");
    document.querySelector("#campo-trimestre-reporte").classList.toggle("oculto", tipo !== "trimestral");
}

// ============================================================
// BLOQUE: PRESENTACION DEL REPORTE FINANCIERO
// Convierte la respuesta de la fachada en indicadores, comparaciones y
// una tabla imprimible sin realizar calculos financieros en el navegador.
// Cumple: RF-05 a RF-09 y CU-06 a CU-09.
// ============================================================
function mostrarReporte(reporte) {
    estado.reporte = reporte;
    const maximoFilial = Math.max(
        ...reporte.comparativo_filiales.map((item) => Number(item.total_eur)),
        0,
    );
    const barras = reporte.comparativo_filiales.length
        ? reporte.comparativo_filiales.map((item) => {
            const porcentaje = maximoFilial > 0 ? (Number(item.total_eur) / maximoFilial) * 100 : 0;
            return `
                <div class="barra-filial">
                    <strong>${textoSeguro(item.filial)}</strong>
                    <span class="pista-barra"><span class="valor-barra" style="width:${porcentaje.toFixed(2)}%"></span></span>
                    <span>${formatearImporte(item.total_eur, "EUR")}</span>
                </div>`;
        }).join("")
        : '<p class="estado-vacio visible">No existen ventas para comparar.</p>';

    const filas = reporte.ventas.map((venta) => `
        <tr>
            <td data-label="Factura"><strong>${textoSeguro(venta.numero_factura)}</strong><br><small>${formatearFecha(venta.fecha_venta, true)}</small></td>
            <td data-label="Filial">${textoSeguro(venta.filial)}</td>
            <td data-label="Producto">${textoSeguro(venta.producto)}<br><small>${textoSeguro(venta.categoria)}</small></td>
            <td data-label="Cantidad">${venta.cantidad}</td>
            <td data-label="Venta local">${formatearImporte(venta.total_local, venta.codigo_divisa)}</td>
            <td data-label="Ingreso EUR">${formatearImporte(venta.total_eur, "EUR")}</td>
            <td data-label="Gasto EUR">${formatearImporte(venta.gasto_eur, "EUR")}</td>
        </tr>`).join("");

    const firma = reporte.firma ? `
        <section class="firma-reporte">
            <h4>Firma digital académica</h4>
            <p><strong>Emisor:</strong> ${textoSeguro(reporte.firma.emisor)}</p>
            <p><strong>Fecha:</strong> ${textoSeguro(reporte.firma.fecha)}</p>
            <p><strong>Identificador:</strong> ${textoSeguro(reporte.firma.identificador)}</p>
            <p><strong>SHA-256:</strong> ${textoSeguro(reporte.firma.sha256)}</p>
        </section>` : "";
    const claseResultado = Number(reporte.resultado_financiero_eur) >= 0
        ? "resultado-positivo"
        : "resultado-negativo";

    document.querySelector("#resultado-reporte").innerHTML = `
        <article class="reporte-documento" id="reporte-imprimible">
            ${reporte.con_marca_agua ? '<div class="marca-agua-reporte">CONFIDENCIAL</div>' : ""}
            <div class="contenido-reporte">
                <header class="cabecera-reporte">
                    <div><p class="etiqueta">FinanCorp S.A. · SERF</p><h3>${textoSeguro(reporte.titulo)}</h3><p>${textoSeguro(reporte.periodo)} · ${textoSeguro(reporte.alcance)}</p></div>
                    <div class="datos-emision"><strong>Generado ${formatearFecha(reporte.fecha_generacion, true)}</strong><span>Desde ${formatearFecha(reporte.fecha_inicio)} hasta ${formatearFecha(reporte.fecha_fin)}</span></div>
                </header>
                <div class="acciones-reporte"><button class="boton boton-secundario" id="boton-imprimir-reporte" type="button">Imprimir o guardar como PDF</button></div>
                <section class="metricas-reporte">
                    <div class="metrica-reporte"><span>Ingresos</span><strong>${formatearImporte(reporte.total_ingresos_eur, "EUR")}</strong></div>
                    <div class="metrica-reporte"><span>Gastos de importación</span><strong>${formatearImporte(reporte.total_gastos_eur, "EUR")}</strong></div>
                    <div class="metrica-reporte ${claseResultado}"><span>Resultado financiero</span><strong>${formatearImporte(reporte.resultado_financiero_eur, "EUR")}</strong></div>
                    <div class="metrica-reporte"><span>Ventas</span><strong>${reporte.cantidad_ventas}</strong></div>
                </section>
                <section class="seccion-reporte"><h4>Comparación de ingresos por filial</h4><div class="grafico-filiales">${barras}</div></section>
                <section class="seccion-reporte">
                    <h4>Detalle de ventas del periodo</h4>
                    <div class="tabla-contenedor"><table><thead><tr><th>Factura</th><th>Filial</th><th>Producto</th><th>Cantidad</th><th>Venta local</th><th>Ingreso EUR</th><th>Gasto EUR</th></tr></thead><tbody>${filas}</tbody></table></div>
                    ${filas ? "" : '<p class="estado-vacio visible">Periodo sin movimientos registrados.</p>'}
                </section>
                ${firma}
                <details class="detalle-patrones"><summary>Ver estructura consolidada del reporte</summary><pre>${textoSeguro(reporte.contenido_emitido)}</pre></details>
            </div>
        </article>`;
    document.querySelector("#boton-imprimir-reporte").addEventListener("click", () => window.print());
}

// ============================================================
// BLOQUE: FORMULARIOS DE LOS PROCESOS DEL NEGOCIO
// Cada envio conserva los datos cuando existe un error y actualiza las
// tablas solamente despues de recibir la confirmacion del backend.
// ============================================================
function prepararFormularios() {
    document.querySelector("#formulario-tasa").addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const formulario = evento.currentTarget;
        bloquearBoton(formulario, true);
        try {
            const respuesta = await solicitar("/api/configuracion/tipos-cambio", { method: "POST", body: JSON.stringify(datosFormulario(formulario)) });
            formulario.reset();
            formulario.elements.fecha_vigencia.value = hoyISO();
            await actualizarDatosGenerales();
            mostrarNotificacion(respuesta.mensaje);
        } catch (error) { mostrarNotificacion(error.message, true); }
        finally { bloquearBoton(formulario, false); }
    });

    document.querySelector("#formulario-filial").addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const formulario = evento.currentTarget;
        bloquearBoton(formulario, true);
        try {
            const respuesta = await solicitar("/api/configuracion/filiales", { method: "POST", body: JSON.stringify(datosFormulario(formulario)) });
            formulario.reset();
            await actualizarDatosGenerales();
            mostrarNotificacion(respuesta.mensaje);
        } catch (error) { mostrarNotificacion(error.message, true); }
        finally { bloquearBoton(formulario, false); }
    });

    document.querySelector("#formulario-producto").addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const formulario = evento.currentTarget;
        bloquearBoton(formulario, true);
        try {
            const respuesta = await solicitar("/api/productos", { method: "POST", body: JSON.stringify(datosFormulario(formulario)) });
            formulario.reset();
            formulario.elements.fecha_importacion.value = hoyISO();
            await actualizarDatosGenerales();
            mostrarNotificacion(respuesta.mensaje);
        } catch (error) { mostrarNotificacion(error.message, true); }
        finally { bloquearBoton(formulario, false); }
    });

    document.querySelector("#formulario-reposicion").addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const formulario = evento.currentTarget;
        bloquearBoton(formulario, true);
        try {
            const datos = datosFormulario(formulario);
            const respuesta = await solicitar("/api/inventario/reponer", { method: "POST", body: JSON.stringify(datos) });
            formulario.elements.cantidad.value = "";
            await cargarInventario(datos.id_filial);
            mostrarNotificacion(respuesta.mensaje);
        } catch (error) { mostrarNotificacion(error.message, true); }
        finally { bloquearBoton(formulario, false); }
    });

    document.querySelector("#formulario-venta").addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const formulario = evento.currentTarget;
        bloquearBoton(formulario, true);
        try {
            const respuesta = await solicitar("/api/ventas", { method: "POST", body: JSON.stringify(datosFormulario(formulario)) });
            mostrarResumenVenta(respuesta.datos);
            const idFilial = formulario.elements.id_filial.value;
            formulario.reset();
            formulario.elements.fecha_venta.value = fechaHoraLocal();
            await prepararVentaPorFilial("");
            await cargarVentas();
            if (document.querySelector("#filtro-filial-inventario").value === idFilial) await cargarInventario(idFilial);
            mostrarNotificacion(respuesta.mensaje);
        } catch (error) { mostrarNotificacion(error.message, true); }
        finally { bloquearBoton(formulario, false); }
    });

    document.querySelector("#formulario-reporte").addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const formulario = evento.currentTarget;
        bloquearBoton(formulario, true);
        try {
            const datos = datosFormulario(formulario);
            datos.con_marca_agua = formulario.elements.con_marca_agua.checked;
            datos.con_firma = formulario.elements.con_firma.checked;
            const respuesta = await solicitar("/api/reportes/generar", {
                method: "POST",
                body: JSON.stringify(datos),
            });
            mostrarReporte(respuesta.datos);
            mostrarNotificacion(respuesta.mensaje);
        } catch (error) { mostrarNotificacion(error.message, true); }
        finally { bloquearBoton(formulario, false); }
    });
}

function prepararEventosDeConsulta() {
    document.querySelector("#buscar-producto").addEventListener("input", (evento) => mostrarProductos(evento.target.value));
    document.querySelector("#boton-consultar-inventario").addEventListener("click", async () => {
        const filial = document.querySelector("#filtro-filial-inventario").value;
        if (!filial) return mostrarNotificacion("Selecciona una filial.", true);
        try { await cargarInventario(filial); }
        catch (error) { mostrarNotificacion(error.message, true); }
    });
    document.querySelector("#formulario-reposicion [name='id_filial']").addEventListener("change", async (evento) => {
        try { await cargarInventario(evento.target.value); }
        catch (error) { mostrarNotificacion(error.message, true); }
    });
    document.querySelector("#filial-venta").addEventListener("change", async (evento) => {
        try { await prepararVentaPorFilial(evento.target.value); }
        catch (error) { mostrarNotificacion(error.message, true); }
    });
    document.querySelector("#producto-venta").addEventListener("change", actualizarDetalleStock);
    document.querySelector("#boton-consultar-ventas").addEventListener("click", async () => {
        try { await cargarVentas(); }
        catch (error) { mostrarNotificacion(error.message, true); }
    });
    document.querySelector("#tipo-reporte").addEventListener("change", actualizarCamposPeriodoReporte);
}

async function iniciarAplicacion() {
    prepararNavegacion();
    prepararFormularios();
    prepararEventosDeConsulta();
    document.querySelector("#fecha-actual").textContent = new Intl.DateTimeFormat("es-PE", { dateStyle: "full" }).format(new Date());
    document.querySelector("#formulario-tasa [name='fecha_vigencia']").value = hoyISO();
    document.querySelector("#formulario-producto [name='fecha_importacion']").value = hoyISO();
    document.querySelector("#formulario-venta [name='fecha_venta']").value = fechaHoraLocal();
    document.querySelector("#ventas-desde").value = inicioMesISO();
    document.querySelector("#ventas-hasta").value = hoyISO();
    const ahora = new Date();
    document.querySelector("#anio-reporte").value = ahora.getFullYear();
    document.querySelector("#mes-reporte").value = String(ahora.getMonth() + 1);
    document.querySelector("#trimestre-reporte").value = String(Math.ceil((ahora.getMonth() + 1) / 3));
    actualizarCamposPeriodoReporte();

    try {
        await actualizarDatosGenerales();
        await cargarVentas();
    } catch (error) {
        mostrarNotificacion(error.message, true);
    }
}

document.addEventListener("DOMContentLoaded", iniciarAplicacion);
