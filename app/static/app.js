const listaProductos = document.querySelector("#lista-productos");
const totalProductos = document.querySelector("#total-productos");
const mensaje = document.querySelector("#mensaje");
const formulario = document.querySelector("#formulario-producto");
const dialogoProducto = document.querySelector("#dialogo-producto");
const selectorCategoria = document.querySelector("#id_categoria");
const selectorProveedor = document.querySelector("#id_proveedor");
const tituloFormulario = document.querySelector("#titulo-formulario");
const botonGuardar = document.querySelector("#guardar-producto");
const botonCancelar = document.querySelector("#cancelar-edicion");
const botonAbrir = document.querySelector("#abrir-formulario");
const botonCerrar = document.querySelector("#cerrar-dialogo");
const formatoPrecio = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});
const formatoCantidad = new Intl.NumberFormat("es-CO", {
  maximumFractionDigits: 3,
});

let idProductoEnEdicion = null;

function mostrarMensaje(texto, tipo = "danger") {
  mensaje.textContent = texto;
  mensaje.className = `alert alert-${tipo}`;
}

function ocultarMensaje() {
  mensaje.textContent = "";
  mensaje.className = "alert d-none";
}

async function solicitar(url, opciones = {}) {
  const respuesta = await fetch(url, opciones);
  if (!respuesta.ok) {
    const detalle = await respuesta.json().catch(() => null);
    throw new Error(detalle?.detail || `Error HTTP ${respuesta.status}`);
  }
  if (respuesta.status === 204) return null;
  return respuesta.json();
}

function agregarCelda(fila, texto, clase = "") {
  const celda = document.createElement("td");
  celda.textContent = texto;
  if (clase) celda.className = clase;
  fila.append(celda);
}

function agregarBoton(fila, texto, clase, accion) {
  const boton = document.createElement("button");
  boton.type = "button";
  boton.textContent = texto;
  boton.className = `btn btn-sm ${clase} me-1`;
  boton.addEventListener("click", accion);
  const celda = fila.lastElementChild;
  celda.append(boton);
}

function crearFila(producto) {
  const fila = document.createElement("tr");
  agregarCelda(fila, String(producto.id_producto), "ps-3 text-secondary");
  agregarCelda(fila, producto.nombre, "fw-medium");
  agregarCelda(fila, producto.categoria);
  agregarCelda(fila, producto.proveedor);
  agregarCelda(fila, producto.unidad);
  agregarCelda(fila, formatoPrecio.format(producto.precio_venta), "text-end");
  agregarCelda(fila, formatoCantidad.format(producto.stock_actual), "text-end");
  agregarCelda(fila, formatoCantidad.format(producto.stock_minimo), "text-end");
  agregarCelda(fila, producto.activo ? "Activo" : "Inactivo");
  fila.lastElementChild.classList.add("pe-3");
  fila.append(document.createElement("td"));
  agregarBoton(fila, "Editar", "btn-outline-primary", () => editarProducto(producto));
  agregarBoton(fila, "Eliminar", "btn-outline-danger", () => borrarProducto(producto));
  fila.lastElementChild.classList.add("pe-3");
  return fila;
}

async function cargarCatalogos() {
  const catalogos = await solicitar("/catalogos");
  agregarOpciones(selectorCategoria, catalogos.categorias, "id_categoria");
  agregarOpciones(selectorProveedor, catalogos.proveedores, "id_proveedor");
}

function agregarOpciones(selector, opciones, propiedadId) {
  for (const opcion of opciones) {
    const elemento = document.createElement("option");
    elemento.value = opcion[propiedadId];
    elemento.textContent = opcion.nombre;
    selector.append(elemento);
  }
}

async function cargarProductos() {
  ocultarMensaje();
  try {
    const productos = await solicitar("/productos");
    listaProductos.replaceChildren();
    if (productos.length === 0) {
      const fila = document.createElement("tr");
      const celda = document.createElement("td");
      celda.colSpan = 10;
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

function editarProducto(producto) {
  idProductoEnEdicion = producto.id_producto;
  formulario.elements.nombre.value = producto.nombre;
  formulario.elements.id_categoria.value = producto.id_categoria;
  formulario.elements.id_proveedor.value = producto.id_proveedor;
  formulario.elements.unidad.value = producto.unidad;
  formulario.elements.precio_venta.value = producto.precio_venta;
  formulario.elements.stock_actual.value = producto.stock_actual;
  formulario.elements.stock_minimo.value = producto.stock_minimo;
  formulario.elements.activo.checked = producto.activo;
  tituloFormulario.textContent = `Editar producto #${producto.id_producto}`;
  botonGuardar.textContent = "Guardar cambios";
  botonCancelar.classList.remove("d-none");
  dialogoProducto.showModal();
}

function agregarProducto() {
  cancelarEdicion();
  dialogoProducto.showModal();
}

function cancelarEdicion() {
  if (dialogoProducto.open) {
    dialogoProducto.close();
    return;
  }
  limpiarFormulario();
}

function limpiarFormulario() {
  idProductoEnEdicion = null;
  formulario.reset();
  tituloFormulario.textContent = "Agregar producto";
  botonGuardar.textContent = "Guardar producto";
  botonCancelar.classList.add("d-none");
}

function datosDelFormulario() {
  return {
    nombre: formulario.elements.nombre.value.trim(),
    id_categoria: Number(formulario.elements.id_categoria.value),
    id_proveedor: Number(formulario.elements.id_proveedor.value),
    unidad: formulario.elements.unidad.value,
    precio_venta: Number(formulario.elements.precio_venta.value),
    stock_actual: Number(formulario.elements.stock_actual.value),
    stock_minimo: Number(formulario.elements.stock_minimo.value),
    activo: formulario.elements.activo.checked,
  };
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  ocultarMensaje();
  const esEdicion = idProductoEnEdicion !== null;
  const url = esEdicion ? `/productos/${idProductoEnEdicion}` : "/productos";

  try {
    await solicitar(url, {
      method: esEdicion ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datosDelFormulario()),
    });
    dialogoProducto.close();
    cancelarEdicion();
    await cargarProductos();
    mostrarMensaje(esEdicion ? "Producto actualizado." : "Producto creado.", "success");
  } catch (error) {
    mostrarMensaje(`No se pudo guardar el producto: ${error.message}`);
  }
});

async function borrarProducto(producto) {
  if (!confirm(`¿Eliminar "${producto.nombre}"? Esta acción no se puede deshacer.`)) {
    return;
  }

  ocultarMensaje();
  try {
    await solicitar(`/productos/${producto.id_producto}`, { method: "DELETE" });
    if (idProductoEnEdicion === producto.id_producto) cancelarEdicion();
    await cargarProductos();
    mostrarMensaje("Producto eliminado.", "success");
  } catch (error) {
    mostrarMensaje(`No se pudo eliminar el producto: ${error.message}`);
  }
}

botonAbrir.addEventListener("click", agregarProducto);
botonCerrar.addEventListener("click", cancelarEdicion);
botonCancelar.addEventListener("click", cancelarEdicion);
dialogoProducto.addEventListener("close", limpiarFormulario);

async function iniciar() {
  try {
    await cargarCatalogos();
    await cargarProductos();
  } catch (error) {
    mostrarMensaje(`No se pudieron cargar categorías y proveedores: ${error.message}`);
  }
}

iniciar();
