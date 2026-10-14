const listaProductos = document.querySelector("#lista-productos");
const totalProductos = document.querySelector("#total-productos");
const mensaje = document.querySelector("#mensaje");
const formatoPrecio = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});

function mostrarMensaje(texto, tipo = "danger") {
  mensaje.textContent = texto;
  mensaje.className = `alert alert-${tipo}`;
}

function ocultarMensaje() {
  mensaje.textContent = "";
  mensaje.className = "alert d-none";
}

async function solicitar(url) {
  const respuesta = await fetch(url);
  if (!respuesta.ok) {
    const detalle = await respuesta.json().catch(() => null);
    throw new Error(detalle?.detail || `Error HTTP ${respuesta.status}`);
  }
  return respuesta.json();
}

function agregarCelda(fila, texto, clase = "") {
  const celda = document.createElement("td");
  celda.textContent = texto;
  if (clase) celda.className = clase;
  fila.append(celda);
}

function crearFila(producto) {
  const fila = document.createElement("tr");
  agregarCelda(fila, String(producto.id_producto), "ps-3 text-secondary");
  agregarCelda(fila, producto.nombre, "fw-medium");
  agregarCelda(fila, producto.categoria);
  agregarCelda(fila, producto.proveedor);
  agregarCelda(fila, producto.unidad);
  agregarCelda(fila, formatoPrecio.format(producto.precio_venta), "text-end");
  agregarCelda(fila, String(producto.stock_actual), "text-end");
  agregarCelda(fila, String(producto.stock_minimo), "text-end");
  agregarCelda(fila, producto.activo ? "Activo" : "Inactivo", "pe-3");
  return fila;
}

async function cargarProductos() {
  ocultarMensaje();
  try {
    const productos = await solicitar("/productos");
    listaProductos.replaceChildren();
    if (productos.length === 0) {
      const fila = document.createElement("tr");
      const celda = document.createElement("td");
      celda.colSpan = 9;
      celda.className = "text-center text-secondary py-4";
      celda.textContent = "No hay productos disponibles.";
      fila.append(celda);
      listaProductos.append(fila);
    } else {
      listaProductos.append(...productos.map(crearFila));
    }
    totalProductos.textContent =
      `${productos.length} ${productos.length === 1 ? "producto" : "productos"}`;
  } catch (error) {
    mostrarMensaje(`No se pudieron cargar los productos: ${error.message}`);
    listaProductos.replaceChildren();
    totalProductos.textContent = "";
  }
}

cargarProductos();
