"use strict";

const estado = {
    filiales: [],
    tasas: [],
    productos: [],
    inventariosProductos: [],
    inventario: [],
    ventas: [],
    ventasResumen: [],
    reporte: null,
};

const esAdministrador = document.body.dataset.esAdministrador === "true";
const registrosPorPagina = 10;
const paginasActuales = {
    tasas: 1,
    filiales: 1,
    productos: 1,
    inventario: 1,
    ventas: 1,
    reportes: 1,
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
    if (bloquear) {
        boton.dataset.textoOriginal = boton.textContent;
        boton.textContent = "Procesando...";
    } else {
        if (boton.textContent === "Procesando...") {
            boton.textContent = boton.dataset.textoOriginal || boton.textContent;
        }
        delete boton.dataset.textoOriginal;
    }
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

function formatearFechaReporte(valor) {
    if (!valor) return "—";
    return new Intl.DateTimeFormat("es-PE", { dateStyle: "short" }).format(new Date(valor));
}

function obtenerFilial(idFilial) {
    return estado.filiales.find((filial) => Number(filial.id_filial) === Number(idFilial));
}

function obtenerProducto(idProducto) {
    return estado.productos.find((producto) => Number(producto.id_producto) === Number(idProducto));
}

function obtenerTasaVigente(codigoDivisa, fechaReferencia) {
    const tasas = estado.tasas
        .filter((tasa) => tasa.activa
            && tasa.codigo_divisa_origen === codigoDivisa
            && tasa.fecha_vigencia <= fechaReferencia)
        .sort((primera, segunda) => segunda.fecha_vigencia.localeCompare(primera.fecha_vigencia));
    return tasas[0] ? Number(tasas[0].tasa) : null;
}

function calcularPrecioVentaProducto() {
    const formulario = document.querySelector("#formulario-producto");
    const campoPrecio = formulario.elements.precio_venta_local;
    const costoCny = Number(formulario.elements.costo_unitario_cny.value);
    const filial = obtenerFilial(formulario.elements.id_filial.value);
    const fecha = formulario.elements.fecha_importacion.value;

    if (!Number.isFinite(costoCny) || costoCny <= 0 || !filial || !fecha) {
        campoPrecio.value = "";
        return;
    }

    const tasaCny = obtenerTasaVigente("CNY", fecha);
    const tasaLocal = filial.codigo_divisa === "EUR"
        ? 1
        : obtenerTasaVigente(filial.codigo_divisa, fecha);
    if (!tasaCny || !tasaLocal) {
        campoPrecio.value = "";
        return;
    }

    campoPrecio.value = (costoCny * 1.20 * tasaCny / tasaLocal).toFixed(2);
}

function obtenerInventariosProducto(idProducto) {
    return estado.inventariosProductos.filter(
        (item) => Number(item.id_producto) === Number(idProducto),
    );
}

function mostrarFilialesProducto(idProducto) {
    const inventarios = obtenerInventariosProducto(idProducto);
    if (!inventarios.length) return "—";
    return inventarios.map((item) => {
        const filial = obtenerFilial(item.id_filial);
        return `<span class="dato-en-linea">${textoSeguro(filial?.codigo || "Filial")}</span>`;
    }).join("");
}

function mostrarPreciosProducto(idProducto) {
    const inventarios = obtenerInventariosProducto(idProducto);
    if (!inventarios.length) return "—";
    return inventarios.map((item) => {
        const filial = obtenerFilial(item.id_filial);
        return `<span class="dato-en-linea"><strong>${formatearImporte(item.precio_venta_local, filial?.codigo_divisa || "EUR")}</strong></span>`;
    }).join("");
}

function botonesAdministrativos(entidad, identificador, puedeEliminar = true) {
    if (!esAdministrador) return "";
    const eliminar = puedeEliminar
        ? `<button class="boton-tabla boton-tabla-peligro" type="button" data-accion-administrativa="eliminar" data-entidad="${entidad}" data-id="${identificador}">Eliminar</button>`
        : "";
    return `<div class="acciones-tabla"><button class="boton-tabla" type="button" data-accion-administrativa="editar" data-entidad="${entidad}" data-id="${identificador}">Editar</button>${eliminar}</div>`;
}

// ============================================================
// BLOQUE: PAGINACION SENCILLA DE LAS TABLAS
// Este bloque divide los registros en grupos de diez y permite
// avanzar o retroceder sin alterar la informacion original.
// ============================================================
function obtenerPagina(registros, modulo) {
    const totalPaginas = Math.max(1, Math.ceil(registros.length / registrosPorPagina));
    paginasActuales[modulo] = Math.min(Math.max(paginasActuales[modulo], 1), totalPaginas);
    const inicio = (paginasActuales[modulo] - 1) * registrosPorPagina;
    return registros.slice(inicio, inicio + registrosPorPagina);
}

function mostrarPaginacion(modulo, totalRegistros) {
    const contenedor = document.querySelector(`#paginacion-${modulo}`);
    if (!contenedor) return;
    const totalPaginas = Math.ceil(totalRegistros / registrosPorPagina);
    if (totalPaginas <= 1) {
        contenedor.innerHTML = "";
        return;
    }
    const pagina = paginasActuales[modulo];
    contenedor.innerHTML = `
        <button class="boton-paginacion" type="button" data-paginacion="${modulo}" data-pagina="${pagina - 1}" ${pagina === 1 ? "disabled" : ""}>Anterior</button>
        <span>Página ${pagina} de ${totalPaginas}</span>
        <button class="boton-paginacion" type="button" data-paginacion="${modulo}" data-pagina="${pagina + 1}" ${pagina === totalPaginas ? "disabled" : ""}>Siguiente</button>`;
}

function mostrarModuloPaginado(modulo) {
    if (modulo === "tasas") mostrarTasas();
    if (modulo === "filiales") mostrarFiliales();
    if (modulo === "productos") mostrarProductos(document.querySelector("#buscar-producto").value);
    if (modulo === "inventario") mostrarInventario();
    if (modulo === "ventas") mostrarVentas();
    if (modulo === "reportes") mostrarHojaReporte();
}

function manejarPaginacion(evento) {
    const boton = evento.target.closest("[data-paginacion]");
    if (!boton || boton.disabled) return;
    const modulo = boton.dataset.paginacion;
    paginasActuales[modulo] = Number(boton.dataset.pagina);
    mostrarModuloPaginado(modulo);
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

// ============================================================
// BLOQUE: BARRA LATERAL COMPACTA EN ESCRITORIO
// Guarda la preferencia para conservar el mismo tamaño al volver a entrar.
// ============================================================
function cambiarTamanioBarra(contraida) {
    const barra = document.querySelector("#barra-lateral");
    const boton = document.querySelector("#boton-contraer-barra");
    barra.classList.toggle("contraida", contraida);
    boton.setAttribute("aria-expanded", String(!contraida));
    boton.setAttribute("aria-label", contraida ? "Expandir menú" : "Contraer menú");
    boton.title = contraida ? "Expandir menú" : "Contraer menú";
    localStorage.setItem("serfBarraContraida", String(contraida));
}

function prepararNavegacion() {
    document.querySelectorAll("[data-seccion]").forEach((boton) => {
        boton.addEventListener("click", () => mostrarSeccion(boton.dataset.seccion));
    });
    document.querySelectorAll("[data-ir-a]").forEach((boton) => {
        boton.addEventListener("click", () => mostrarSeccion(boton.dataset.irA));
    });
    document.querySelector("#boton-menu").addEventListener("click", () => {
        const barra = document.querySelector("#barra-lateral");
        const abierta = barra.classList.toggle("abierta");
        document.querySelector("#fondo-menu").classList.toggle("visible", abierta);
        document.querySelector("#boton-menu").setAttribute("aria-expanded", String(abierta));
    });
    document.querySelector("#fondo-menu").addEventListener("click", cerrarMenuMovil);
    const barraContraida = localStorage.getItem("serfBarraContraida") === "true";
    cambiarTamanioBarra(barraContraida);
    document.querySelector("#boton-contraer-barra").addEventListener("click", () => {
        cambiarTamanioBarra(!document.querySelector("#barra-lateral").classList.contains("contraida"));
    });
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

// ============================================================
// BLOQUE: GRAFICOS DEL RESUMEN GENERAL
// Agrupa los datos reales para mostrar los seis analisis principales.
// ============================================================
function mostrarGraficoVacio(id) {
    document.querySelector(id).innerHTML = '<div class="grafico-vacio">No existen datos para mostrar.</div>';
}

function crearBarrasHorizontales(datos, formatearValor) {
    if (!datos.length) return '<div class="grafico-vacio">No existen datos para mostrar.</div>';
    const maximo = Math.max(...datos.map((item) => Number(item.valor)), 1);
    return `<div class="lista-barras-dashboard">${datos.map((item) => `
        <div class="fila-barra-dashboard">
            <strong title="${textoSeguro(item.nombre)}">${textoSeguro(item.nombre)}</strong>
            <span class="carril-dashboard"><span class="relleno-dashboard" style="width:${Math.max((Number(item.valor) / maximo) * 100, 1)}%"></span></span>
            <span>${formatearValor(item.valor)}</span>
        </div>`).join("")}</div>`;
}

function mostrarDashboardFiliales() {
    const acumulado = new Map();
    estado.ventasResumen.forEach((venta) => {
        acumulado.set(venta.id_filial, (acumulado.get(venta.id_filial) || 0) + Number(venta.total_eur));
    });
    const datos = [...acumulado.entries()]
        .map(([idFilial, valor]) => ({ nombre: obtenerFilial(idFilial)?.nombre || `Filial ${idFilial}`, valor }))
        .sort((primero, segundo) => segundo.valor - primero.valor);
    document.querySelector("#dashboard-filiales").innerHTML = crearBarrasHorizontales(
        datos,
        (valor) => formatearImporte(valor, "EUR"),
    );
}

function mostrarDashboardEvolucion() {
    if (!estado.ventasResumen.length) return mostrarGraficoVacio("#dashboard-evolucion");
    const meses = Array(12).fill(0);
    estado.ventasResumen.forEach((venta) => {
        const mes = new Date(venta.fecha_venta).getMonth();
        meses[mes] += Number(venta.total_eur);
    });
    const maximo = Math.max(...meses, 1);
    const ancho = 700;
    const alto = 210;
    const margenX = 35;
    const margenY = 22;
    const puntos = meses.map((valor, indice) => {
        const x = margenX + (indice * (ancho - margenX * 2) / 11);
        const y = alto - margenY - ((valor / maximo) * (alto - margenY * 2));
        return { x, y, valor };
    });
    const nombresMes = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];
    document.querySelector("#dashboard-evolucion").innerHTML = `
        <svg class="linea-dashboard" viewBox="0 0 ${ancho} 245" role="img" aria-label="Evolución mensual de ventas">
            <line class="guia" x1="${margenX}" y1="${alto - margenY}" x2="${ancho - margenX}" y2="${alto - margenY}"></line>
            <polyline class="trazo" points="${puntos.map((punto) => `${punto.x},${punto.y}`).join(" ")}"></polyline>
            ${puntos.map((punto, indice) => `<circle class="punto" cx="${punto.x}" cy="${punto.y}" r="5"><title>${nombresMes[indice]}: ${formatearImporte(punto.valor, "EUR")}</title></circle>`).join("")}
            ${puntos.map((punto, indice) => `<text x="${punto.x}" y="235" text-anchor="middle">${nombresMes[indice]}</text>`).join("")}
        </svg>`;
}

function mostrarDashboardInventario() {
    const cantidades = { disponible: 0, bajo: 0, agotado: 0 };
    estado.inventariosProductos.forEach((item) => {
        const stock = Number(item.stock_disponible);
        if (stock === 0) cantidades.agotado += 1;
        else if (stock <= 10) cantidades.bajo += 1;
        else cantidades.disponible += 1;
    });
    const total = cantidades.disponible + cantidades.bajo + cantidades.agotado;
    if (!total) return mostrarGraficoVacio("#dashboard-inventario");
    const disponible = (cantidades.disponible / total) * 100;
    const bajo = (cantidades.bajo / total) * 100;
    document.querySelector("#dashboard-inventario").innerHTML = `
        <div class="resumen-dona-dashboard">
            <div class="dona-dashboard" style="background:conic-gradient(#5ba897 0 ${disponible}%, #e3b65d ${disponible}% ${disponible + bajo}%, #df8a8a ${disponible + bajo}% 100%)">
                <div class="centro-dona"><strong>${total}</strong><span>Productos</span></div>
            </div>
            <div class="leyenda-dashboard">
                <div class="item-leyenda"><i style="background:#5ba897"></i><span>Disponible</span><strong>${cantidades.disponible}</strong></div>
                <div class="item-leyenda"><i style="background:#e3b65d"></i><span>Stock bajo</span><strong>${cantidades.bajo}</strong></div>
                <div class="item-leyenda"><i style="background:#df8a8a"></i><span>Sin stock</span><strong>${cantidades.agotado}</strong></div>
            </div>
        </div>`;
}

function detallesVentasResumen() {
    return estado.ventasResumen.flatMap((venta) => venta.detalles || []);
}

function mostrarDashboardProductos() {
    const acumulado = new Map();
    detallesVentasResumen().forEach((detalle) => {
        acumulado.set(detalle.id_producto, (acumulado.get(detalle.id_producto) || 0) + Number(detalle.cantidad));
    });
    const datos = [...acumulado.entries()]
        .map(([idProducto, valor]) => ({ nombre: obtenerProducto(idProducto)?.nombre || `Producto ${idProducto}`, valor }))
        .sort((primero, segundo) => segundo.valor - primero.valor)
        .slice(0, 5);
    document.querySelector("#dashboard-productos").innerHTML = crearBarrasHorizontales(
        datos,
        (valor) => `${valor} unid.`,
    );
}

function crearBarrasVerticales(datos, formatearValor, clasePorDato = () => "") {
    if (!datos.length) return '<div class="grafico-vacio">No existen datos para mostrar.</div>';
    const maximo = Math.max(...datos.map((item) => Math.abs(Number(item.valor))), 1);
    return `<div class="barras-verticales-dashboard">${datos.map((item) => `
        <div class="columna-dashboard">
            <strong>${formatearValor(item.valor)}</strong>
            <div class="espacio-barra-vertical"><span class="barra-vertical ${clasePorDato(item)}" style="height:${Math.max((Math.abs(Number(item.valor)) / maximo) * 100, 2)}%"></span></div>
            <span>${textoSeguro(item.nombre)}</span>
        </div>`).join("")}</div>`;
}

function mostrarDashboardCategorias() {
    const acumulado = new Map();
    detallesVentasResumen().forEach((detalle) => {
        const categoria = obtenerProducto(detalle.id_producto)?.categoria || "Sin categoría";
        acumulado.set(categoria, (acumulado.get(categoria) || 0) + Number(detalle.cantidad));
    });
    const datos = [...acumulado.entries()]
        .map(([nombre, valor]) => ({ nombre, valor }))
        .sort((primero, segundo) => segundo.valor - primero.valor);
    document.querySelector("#dashboard-categorias").innerHTML = crearBarrasVerticales(
        datos,
        (valor) => `${valor}`,
        () => "verde",
    );
}

function mostrarDashboardFinanciero() {
    const ingresos = estado.ventasResumen.reduce((total, venta) => total + Number(venta.total_eur), 0);
    const gastos = estado.ventasResumen.reduce((total, venta) => total + Number(venta.total_costo_eur), 0);
    const resultado = ingresos - gastos;
    const datos = [
        { nombre: "Ingresos", valor: ingresos, clase: "verde" },
        { nombre: "Gastos", valor: gastos, clase: "" },
        { nombre: "Resultado", valor: resultado, clase: resultado < 0 ? "roja" : "verde" },
    ];
    document.querySelector("#dashboard-financiero").innerHTML = crearBarrasVerticales(
        datos,
        (valor) => formatearImporte(valor, "EUR"),
        (item) => item.clase,
    );
}

function mostrarDashboards() {
    mostrarDashboardFiliales();
    mostrarDashboardEvolucion();
    mostrarDashboardInventario();
    mostrarDashboardProductos();
    mostrarDashboardCategorias();
    mostrarDashboardFinanciero();
}

function mostrarFiliales() {
    const cuerpo = document.querySelector("#tabla-filiales");
    const filialesActivas = estado.filiales.filter((filial) => filial.activa);
    const filialesPagina = obtenerPagina(filialesActivas, "filiales");
    cuerpo.innerHTML = filialesPagina.map((filial) => `
        <tr>
            <td data-label="Código"><strong>${textoSeguro(filial.codigo)}</strong></td>
            <td data-label="Filial">${textoSeguro(filial.nombre)}</td>
            <td data-label="Ubicación">${textoSeguro(filial.ciudad)}, ${textoSeguro(filial.pais)}</td>
            <td data-label="Moneda"><span class="insignia insignia-neutra">${textoSeguro(filial.codigo_divisa)}</span></td>
            ${esAdministrador ? `<td data-label="Acciones">${botonesAdministrativos("filial", filial.id_filial)}</td>` : ""}
        </tr>`).join("");
    document.querySelector("#vacio-filiales").classList.toggle("visible", filialesActivas.length === 0);
    mostrarPaginacion("filiales", filialesActivas.length);
    llenarSelectoresFiliales();
}

function mostrarTasas() {
    const tasasPagina = obtenerPagina(estado.tasas, "tasas");
    document.querySelector("#tabla-tasas").innerHTML = tasasPagina.map((tasa) => `
        <tr>
            <td data-label="Divisa"><strong>${textoSeguro(tasa.codigo_divisa_origen)}/EUR</strong></td>
            <td data-label="Tasa EUR">${textoSeguro(tasa.tasa)}</td>
            <td data-label="Vigencia">${formatearFecha(tasa.fecha_vigencia)}</td>
            <td data-label="Estado"><span class="insignia ${tasa.activa ? "insignia-correcta" : "insignia-neutra"}">${tasa.activa && tasa.fecha_vigencia > hoyISO() ? "Programada" : (tasa.activa ? "Activa" : "Histórica")}</span></td>
            ${esAdministrador ? `<td data-label="Acciones">${tasa.activa && tasa.codigo_divisa_origen !== "EUR" ? botonesAdministrativos("tasa", tasa.id_tipo_cambio) : ""}</td>` : ""}
        </tr>`).join("");
    document.querySelector("#vacio-tasas").classList.toggle("visible", estado.tasas.length === 0);
    mostrarPaginacion("tasas", estado.tasas.length);
}

function mostrarProductos(filtro = "") {
    const texto = filtro.trim().toLowerCase();
    const productos = estado.productos.filter((producto) => producto.activo && (
        !texto || producto.codigo.toLowerCase().includes(texto) || producto.nombre.toLowerCase().includes(texto)));
    const productosPagina = obtenerPagina(productos, "productos");
    document.querySelector("#tabla-productos").innerHTML = productosPagina.map((producto) => `
        <tr>
            <td data-label="Código"><strong>${textoSeguro(producto.codigo)}</strong></td>
            <td data-label="Producto"><span class="dato-principal"><strong>${textoSeguro(producto.nombre)}</strong><small>${textoSeguro(producto.proveedor)}</small></span></td>
            <td data-label="Categoría">${textoSeguro(producto.categoria)}</td>
            <td data-label="Costo CNY">${formatearImporte(producto.costo_unitario_cny, "CNY")}</td>
            <td data-label="Costo EUR">${formatearImporte(producto.costo_unitario_eur, "EUR")}</td>
            <td data-label="Importación">${formatearFecha(producto.fecha_importacion)}</td>
            <td data-label="Filial">${mostrarFilialesProducto(producto.id_producto)}</td>
            <td data-label="Precio venta">${mostrarPreciosProducto(producto.id_producto)}</td>
            ${esAdministrador ? `<td data-label="Acciones">${botonesAdministrativos("producto", producto.id_producto)}</td>` : ""}
        </tr>`).join("");
    document.querySelector("#vacio-productos").classList.toggle("visible", productos.length === 0);
    mostrarPaginacion("productos", productos.length);
}

function llenarProductosInventario() {
    const selector = document.querySelector("#producto-reposicion");
    const valorActual = selector.value;
    selector.innerHTML = '<option value="">Seleccionar producto</option>' + estado.inventario.filter((item) => obtenerProducto(item.id_producto)?.activo).map((item) => {
        const producto = obtenerProducto(item.id_producto);
        return `<option value="${item.id_producto}">${textoSeguro(producto?.codigo || "")} · ${textoSeguro(producto?.nombre || "Producto")}</option>`;
    }).join("");
    if ([...selector.options].some((opcion) => opcion.value === valorActual)) selector.value = valorActual;
}

function mostrarInventario() {
    const idFilial = document.querySelector("#filtro-filial-inventario").value;
    const filial = obtenerFilial(idFilial);
    document.querySelector("#subtitulo-inventario").textContent = filial
        ? `${filial.nombre} · precios expresados en ${filial.codigo_divisa}`
        : "Selecciona una filial para consultar.";
    const inventarioActivo = estado.inventario.filter((item) => obtenerProducto(item.id_producto)?.activo);
    const inventarioPagina = obtenerPagina(inventarioActivo, "inventario");
    document.querySelector("#tabla-inventario").innerHTML = inventarioPagina.map((item) => {
        const producto = obtenerProducto(item.id_producto);
        const stock = Number(item.stock_disponible);
        let estadoStock = "Disponible";
        let claseEstado = "insignia-correcta";
        if (stock === 0) {
            estadoStock = "Sin stock";
            claseEstado = "insignia-sin-stock";
        } else if (stock <= 10) {
            estadoStock = "Stock bajo";
            claseEstado = "insignia-alerta";
        }
        return `
            <tr>
                <td data-label="Código"><strong>${textoSeguro(producto?.codigo || item.id_producto)}</strong></td>
                <td data-label="Producto">${textoSeguro(producto?.nombre || "Producto")}</td>
                <td data-label="Stock"><strong>${item.stock_disponible}</strong></td>
                <td data-label="Precio local">${formatearImporte(item.precio_venta_local, filial?.codigo_divisa || "EUR")}</td>
                <td data-label="Estado"><span class="insignia ${claseEstado}">${estadoStock}</span></td>
            </tr>`;
    }).join("");
    document.querySelector("#vacio-inventario").classList.toggle("visible", inventarioActivo.length === 0);
    mostrarPaginacion("inventario", inventarioActivo.length);
    llenarProductosInventario();
}

function mostrarVentas() {
    const ventasPagina = obtenerPagina(estado.ventas, "ventas");
    document.querySelector("#tabla-ventas").innerHTML = ventasPagina.map((venta) => {
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
    mostrarPaginacion("ventas", estado.ventas.length);
    mostrarIndicadores();
}

async function cargarInventario(idFilial) {
    paginasActuales.inventario = 1;
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
    paginasActuales.ventas = 1;
    mostrarVentas();
}

async function cargarDatosResumen() {
    const anio = new Date().getFullYear();
    const parametros = new URLSearchParams({
        fecha_inicio: `${anio}-01-01`,
        fecha_fin: hoyISO(),
    });
    const respuesta = await solicitar(`/api/ventas?${parametros}`);
    estado.ventasResumen = respuesta.datos;
    mostrarDashboards();
}

async function actualizarDatosGenerales() {
    const [filiales, tasas, productos, inventariosProductos] = await Promise.all([
        solicitar("/api/configuracion/filiales"),
        solicitar("/api/configuracion/tipos-cambio"),
        solicitar("/api/productos"),
        solicitar("/api/inventario/catalogo"),
    ]);
    estado.filiales = filiales.datos;
    estado.tasas = tasas.datos;
    estado.productos = productos.datos;
    estado.inventariosProductos = inventariosProductos.datos;
    mostrarFiliales();
    mostrarTasas();
    mostrarProductos(document.querySelector("#buscar-producto").value);
    mostrarIndicadores();
    mostrarDashboards();
    calcularPrecioVentaProducto();
}

async function prepararVentaPorFilial(idFilial) {
    const selector = document.querySelector("#producto-venta");
    document.querySelector("#precio-unitario-venta").value = "";
    document.querySelector("#detalle-stock").textContent = "Consultando productos disponibles...";
    if (!idFilial) {
        selector.innerHTML = '<option value="">Seleccionar una filial primero</option>';
        document.querySelector("#detalle-stock").textContent = "Selecciona un producto para consultar su disponibilidad.";
        return;
    }
    const respuesta = await solicitar(`/api/inventario?id_filial=${encodeURIComponent(idFilial)}`);
    const disponibles = respuesta.datos.filter((item) => (
        Number(item.stock_disponible) > 0
        && obtenerProducto(item.id_producto)?.activo
    ));
    selector.innerHTML = '<option value="">Seleccionar producto</option>' + disponibles.map((item) => {
        const producto = obtenerProducto(item.id_producto);
        return `<option value="${item.id_producto}" data-stock="${item.stock_disponible}" data-precio="${item.precio_venta_local}">${textoSeguro(producto?.codigo || "")} · ${textoSeguro(producto?.nombre || "Producto")}</option>`;
    }).join("");
    document.querySelector("#detalle-stock").textContent = disponibles.length
        ? "Selecciona un producto para consultar su disponibilidad."
        : "La filial no tiene productos con stock disponible.";
}

function actualizarDetalleStock() {
    const selector = document.querySelector("#producto-venta");
    const opcion = selector.selectedOptions[0];
    const filial = obtenerFilial(document.querySelector("#filial-venta").value);
    const precioUnitario = document.querySelector("#precio-unitario-venta");
    precioUnitario.value = opcion?.value
        ? formatearImporte(opcion.dataset.precio, filial?.codigo_divisa || "EUR")
        : "";
    document.querySelector("#detalle-stock").textContent = opcion?.value
        ? `Disponible: ${opcion.dataset.stock} unidades`
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
function crearFilasReporte(ventas) {
    return ventas.map((venta) => `
        <tr>
            <td data-label="Factura"><strong>${textoSeguro(venta.numero_factura)}</strong></td>
            <td data-label="Filial" title="${textoSeguro(venta.filial)}">${textoSeguro(venta.filial)}</td>
            <td data-label="Categoría">${textoSeguro(venta.categoria)}</td>
            <td data-label="Producto" title="${textoSeguro(venta.producto)}">${textoSeguro(venta.producto)}</td>
            <td data-label="Fecha">${formatearFechaReporte(venta.fecha_venta)}</td>
            <td data-label="Cantidad">${venta.cantidad}</td>
            <td data-label="Venta local">${formatearImporte(venta.total_local, venta.codigo_divisa)}</td>
            <td data-label="Ingreso EUR">${formatearImporte(venta.total_eur, "EUR")}</td>
            <td data-label="Gasto EUR">${formatearImporte(venta.gasto_eur, "EUR")}</td>
        </tr>`).join("");
}

function crearTablaReporte(ventas) {
    const filas = crearFilasReporte(ventas);
    return `
        <div class="tabla-contenedor tabla-reporte-contenedor">
            <table class="tabla-reporte">
                <thead><tr><th>Factura</th><th>Filial</th><th>Categoría</th><th>Producto</th><th>Fecha</th><th>Cantidad</th><th>Venta local</th><th>Ingreso EUR</th><th>Gasto EUR</th></tr></thead>
                <tbody>${filas}</tbody>
            </table>
        </div>
        ${filas ? "" : '<p class="estado-vacio visible">Periodo sin movimientos registrados.</p>'}`;
}

function crearFirmaReporte(reporte) {
    if (!reporte.firma) return "";
    return `
        <section class="firma-reporte">
            <h4>Firma digital</h4>
            <p><strong>Emisor:</strong> ${textoSeguro(reporte.firma.emisor)}</p>
            <p><strong>Fecha:</strong> ${textoSeguro(reporte.firma.fecha)}</p>
            <p><strong>Identificador:</strong> ${textoSeguro(reporte.firma.identificador)}</p>
            <p><strong>SHA-256:</strong> ${textoSeguro(reporte.firma.sha256)}</p>
        </section>`;
}

function moverFirmaSiNoCabe(marcaAgua, firma) {
    if (!firma) return;
    const documento = document.querySelector("#reporte-imprimible");
    const hojas = documento.querySelectorAll(".hoja-reporte");
    const ultimaHoja = hojas[hojas.length - 1];
    const firmaVisible = ultimaHoja.querySelector(".firma-reporte");
    if (!firmaVisible) return;

    // La hoja se muestra un instante sin ser visible para medir la firma completa.
    const estabaActiva = ultimaHoja.classList.contains("activa");
    if (!estabaActiva) ultimaHoja.classList.add("activa", "hoja-en-medicion");
    const limiteInferior = ultimaHoja.getBoundingClientRect().bottom - 32;
    const firmaNoCabe = firmaVisible.getBoundingClientRect().bottom > limiteInferior;
    if (!estabaActiva) ultimaHoja.classList.remove("activa", "hoja-en-medicion");
    if (!firmaNoCabe) return;

    firmaVisible.remove();
    const hojaFirma = document.createElement("section");
    hojaFirma.className = "hoja-reporte";
    hojaFirma.dataset.pagina = String(hojas.length + 1);
    hojaFirma.innerHTML = `
        ${marcaAgua}
        <div class="contenido-reporte contenido-firma-reporte">
            ${firma}
        </div>`;
    documento.appendChild(hojaFirma);
}

function mostrarHojaReporte() {
    const hojas = document.querySelectorAll("#reporte-imprimible .hoja-reporte");
    if (!hojas.length || !estado.reporte) return;
    paginasActuales.reportes = Math.min(Math.max(paginasActuales.reportes, 1), hojas.length);
    hojas.forEach((hoja) => {
        hoja.classList.toggle("activa", Number(hoja.dataset.pagina) === paginasActuales.reportes);
    });
    const contenedor = document.querySelector("#paginacion-reportes");
    if (hojas.length <= 1) {
        contenedor.innerHTML = "";
        return;
    }
    const pagina = paginasActuales.reportes;
    contenedor.innerHTML = `
        <button class="boton-paginacion" type="button" data-paginacion="reportes" data-pagina="${pagina - 1}" ${pagina === 1 ? "disabled" : ""}>Anterior</button>
        <span>Página ${pagina} de ${hojas.length}</span>
        <button class="boton-paginacion" type="button" data-paginacion="reportes" data-pagina="${pagina + 1}" ${pagina === hojas.length ? "disabled" : ""}>Siguiente</button>`;
}

function mostrarReporte(reporte) {
    estado.reporte = reporte;
    paginasActuales.reportes = 1;
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

    // La primera hoja reserva espacio para el resumen y las siguientes
    // aprovechan casi toda la pagina para mostrar el detalle de ventas.
    const gruposVentas = [reporte.ventas.slice(0, 30)];
    for (let inicio = 30; inicio < reporte.ventas.length; inicio += 40) {
        gruposVentas.push(reporte.ventas.slice(inicio, inicio + 40));
    }
    const totalHojas = gruposVentas.length;
    const marcaAgua = reporte.con_marca_agua
        ? '<div class="marca-agua-reporte">CONFIDENCIAL</div>'
        : "";
    const firma = crearFirmaReporte(reporte);
    const claseResultado = Number(reporte.resultado_financiero_eur) >= 0
        ? "resultado-positivo"
        : "resultado-negativo";

    const hojas = gruposVentas.map((ventasPagina, indice) => {
        const numeroPagina = indice + 1;
        const esPrimera = indice === 0;
        const esUltima = numeroPagina === totalHojas;
        const resumen = esPrimera ? `
            <header class="cabecera-reporte">
                <div><p class="etiqueta">FinanCorp S.A. · SERF</p><h3>${textoSeguro(reporte.titulo)}</h3><p>${textoSeguro(reporte.periodo)} · ${textoSeguro(reporte.alcance)}</p></div>
                <div class="datos-emision"><strong>Generado ${formatearFecha(reporte.fecha_generacion, true)}</strong><span>Desde ${formatearFecha(reporte.fecha_inicio)} hasta ${formatearFecha(reporte.fecha_fin)}</span></div>
            </header>
            <section class="metricas-reporte">
                <div class="metrica-reporte"><span>Ingresos</span><strong>${formatearImporte(reporte.total_ingresos_eur, "EUR")}</strong></div>
                <div class="metrica-reporte"><span>Gastos de importación</span><strong>${formatearImporte(reporte.total_gastos_eur, "EUR")}</strong></div>
                <div class="metrica-reporte ${claseResultado}"><span>Resultado financiero</span><strong>${formatearImporte(reporte.resultado_financiero_eur, "EUR")}</strong></div>
                <div class="metrica-reporte"><span>Ventas</span><strong>${reporte.cantidad_ventas}</strong></div>
            </section>
            <section class="seccion-reporte comparativo-reporte"><h4>Comparación de ingresos por filial</h4><div class="grafico-filiales">${barras}</div></section>` : "";
        return `
            <section class="hoja-reporte ${esPrimera ? "activa" : ""}" data-pagina="${numeroPagina}">
                ${marcaAgua}
                <div class="contenido-reporte">
                    ${resumen}
                    <section class="seccion-reporte detalle-ventas-reporte">
                        <h4>Detalle de ventas del periodo</h4>
                        ${crearTablaReporte(ventasPagina)}
                    </section>
                    ${esUltima ? firma : ""}
                </div>
            </section>`;
    }).join("");

    document.querySelector("#resultado-reporte").innerHTML = `
        <div class="controles-reporte-externos">
            <div class="paginacion paginacion-reporte" id="paginacion-reportes"></div>
            <button class="boton boton-secundario" id="boton-imprimir-reporte" type="button">Imprimir o guardar como PDF</button>
        </div>
        <article class="reporte-documento" id="reporte-imprimible">
            ${hojas}
        </article>`;
    moverFirmaSiNoCabe(marcaAgua, firma);
    document.querySelector("#boton-imprimir-reporte").addEventListener("click", () => window.print());
    mostrarHojaReporte();
}

function restablecerFormularioTasa() {
    const formulario = document.querySelector("#formulario-tasa");
    delete formulario.dataset.id;
    formulario.reset();
    formulario.elements.fecha_vigencia.value = hoyISO();
    document.querySelector("#titulo-formulario-tasa").textContent = "Nueva tasa hacia EUR";
    document.querySelector("#boton-guardar-tasa").textContent = "Guardar tasa";
    document.querySelector("#boton-cancelar-tasa").classList.add("oculto");
}

function restablecerFormularioFilial() {
    const formulario = document.querySelector("#formulario-filial");
    delete formulario.dataset.id;
    formulario.reset();
    document.querySelector("#titulo-formulario-filial").textContent = "Nueva filial";
    document.querySelector("#boton-guardar-filial").textContent = "Registrar filial";
    document.querySelector("#boton-cancelar-filial").classList.add("oculto");
}

function restablecerFormularioProducto() {
    const formulario = document.querySelector("#formulario-producto");
    delete formulario.dataset.id;
    formulario.elements.id_filial.disabled = false;
    formulario.elements.stock_inicial.disabled = false;
    formulario.elements.precio_venta_local.disabled = true;
    formulario.reset();
    formulario.elements.fecha_importacion.value = hoyISO();
    document.querySelector("#titulo-formulario-producto").textContent = "Nuevo producto tecnológico";
    document.querySelector("#ayuda-formulario-producto").textContent = "";
    document.querySelector("#boton-limpiar-producto").textContent = "Limpiar";
    document.querySelector("#boton-guardar-producto").textContent = "Guardar producto";
}

function editarTasa(idTipoCambio) {
    const tasa = estado.tasas.find((item) => Number(item.id_tipo_cambio) === Number(idTipoCambio));
    if (!tasa || !tasa.activa) return;
    const formulario = document.querySelector("#formulario-tasa");
    formulario.dataset.id = tasa.id_tipo_cambio;
    formulario.elements.codigo_divisa_origen.value = tasa.codigo_divisa_origen;
    formulario.elements.tasa.value = tasa.tasa;
    formulario.elements.fecha_vigencia.value = tasa.fecha_vigencia;
    document.querySelector("#titulo-formulario-tasa").textContent = "Editar tasa hacia EUR";
    document.querySelector("#boton-guardar-tasa").textContent = "Guardar cambios";
    document.querySelector("#boton-cancelar-tasa").classList.remove("oculto");
    mostrarSeccion("configuracion");
    formulario.scrollIntoView({ behavior: "smooth", block: "center" });
}

function editarFilial(idFilial) {
    const filial = obtenerFilial(idFilial);
    if (!filial || !filial.activa) return;
    const formulario = document.querySelector("#formulario-filial");
    formulario.dataset.id = filial.id_filial;
    formulario.elements.codigo.value = filial.codigo;
    formulario.elements.codigo_divisa.value = filial.codigo_divisa;
    formulario.elements.nombre.value = filial.nombre;
    formulario.elements.pais.value = filial.pais;
    formulario.elements.ciudad.value = filial.ciudad;
    document.querySelector("#titulo-formulario-filial").textContent = "Editar filial";
    document.querySelector("#boton-guardar-filial").textContent = "Guardar cambios";
    document.querySelector("#boton-cancelar-filial").classList.remove("oculto");
    mostrarSeccion("configuracion");
    formulario.scrollIntoView({ behavior: "smooth", block: "center" });
}

function editarProducto(idProducto) {
    const producto = obtenerProducto(idProducto);
    if (!producto || !producto.activo) return;
    const formulario = document.querySelector("#formulario-producto");
    formulario.dataset.id = producto.id_producto;
    formulario.elements.codigo.value = producto.codigo;
    formulario.elements.nombre.value = producto.nombre;
    formulario.elements.categoria.value = producto.categoria;
    formulario.elements.descripcion_tecnica.value = producto.descripcion_tecnica;
    formulario.elements.costo_unitario_cny.value = producto.costo_unitario_cny;
    formulario.elements.proveedor.value = producto.proveedor;
    formulario.elements.fecha_importacion.value = producto.fecha_importacion;
    formulario.elements.id_filial.disabled = true;
    formulario.elements.stock_inicial.disabled = true;
    formulario.elements.precio_venta_local.disabled = true;
    document.querySelector("#titulo-formulario-producto").textContent = "Editar producto tecnológico";
    document.querySelector("#ayuda-formulario-producto").textContent = "El inventario y el precio local se administran desde su módulo correspondiente.";
    document.querySelector("#boton-limpiar-producto").textContent = "Cancelar";
    document.querySelector("#boton-guardar-producto").textContent = "Guardar cambios";
    mostrarSeccion("productos");
    formulario.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function manejarAccionAdministrativa(evento) {
    const boton = evento.target.closest("[data-accion-administrativa]");
    if (!boton || !esAdministrador) return;
    const accion = boton.dataset.accionAdministrativa;
    const entidad = boton.dataset.entidad;
    const identificador = Number(boton.dataset.id);
    if (accion === "editar") {
        if (entidad === "tasa") editarTasa(identificador);
        if (entidad === "filial") editarFilial(identificador);
        if (entidad === "producto") editarProducto(identificador);
        return;
    }
    const nombres = { tasa: "la tasa", filial: "la filial", producto: "el producto" };
    if (!window.confirm(`¿Deseas eliminar ${nombres[entidad]}? El historial se conservará.`)) return;
    const rutas = {
        tasa: "/api/configuracion/tipos-cambio",
        filial: "/api/configuracion/filiales",
        producto: "/api/productos",
    };
    try {
        const respuesta = await solicitar(`${rutas[entidad]}/${identificador}`, { method: "DELETE" });
        if (entidad === "tasa") restablecerFormularioTasa();
        if (entidad === "filial") restablecerFormularioFilial();
        if (entidad === "producto") restablecerFormularioProducto();
        await actualizarDatosGenerales();
        mostrarNotificacion(respuesta.mensaje);
    } catch (error) {
        mostrarNotificacion(error.message, true);
    }
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
            const id = formulario.dataset.id;
            const ruta = id ? `/api/configuracion/tipos-cambio/${id}` : "/api/configuracion/tipos-cambio";
            const respuesta = await solicitar(ruta, { method: id ? "PUT" : "POST", body: JSON.stringify(datosFormulario(formulario)) });
            restablecerFormularioTasa();
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
            const id = formulario.dataset.id;
            const ruta = id ? `/api/configuracion/filiales/${id}` : "/api/configuracion/filiales";
            const respuesta = await solicitar(ruta, { method: id ? "PUT" : "POST", body: JSON.stringify(datosFormulario(formulario)) });
            restablecerFormularioFilial();
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
            const id = formulario.dataset.id;
            const ruta = id ? `/api/productos/${id}` : "/api/productos";
            const respuesta = await solicitar(ruta, { method: id ? "PUT" : "POST", body: JSON.stringify(datosFormulario(formulario)) });
            restablecerFormularioProducto();
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
            await actualizarDatosGenerales();
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
            await actualizarDatosGenerales();
            await cargarDatosResumen();
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
    document.addEventListener("click", manejarAccionAdministrativa);
    document.addEventListener("click", manejarPaginacion);
    document.querySelector("#boton-cancelar-tasa").addEventListener("click", restablecerFormularioTasa);
    document.querySelector("#boton-cancelar-filial").addEventListener("click", restablecerFormularioFilial);
    document.querySelector("#boton-limpiar-producto").addEventListener("click", restablecerFormularioProducto);
    document.querySelector("#buscar-producto").addEventListener("input", (evento) => {
        paginasActuales.productos = 1;
        mostrarProductos(evento.target.value);
    });
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
    document.querySelector("#formulario-producto [name='costo_unitario_cny']").addEventListener("input", calcularPrecioVentaProducto);
    document.querySelector("#formulario-producto [name='id_filial']").addEventListener("change", calcularPrecioVentaProducto);
    document.querySelector("#formulario-producto [name='fecha_importacion']").addEventListener("change", calcularPrecioVentaProducto);
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
        await cargarDatosResumen();
    } catch (error) {
        mostrarNotificacion(error.message, true);
    }
}

document.addEventListener("DOMContentLoaded", iniciarAplicacion);
