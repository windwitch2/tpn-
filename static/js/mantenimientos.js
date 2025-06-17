// Variables globales
let mantenimientoActualId = null;
const modal = document.getElementById('modalMantenimiento');
const modalConfirmacion = document.getElementById('modalConfirmacion');
const formMantenimiento = document.getElementById('formMantenimiento');
const btnAgregar = document.getElementById('btnAgregarMantenimiento');

// Función para abrir el modal de mantenimiento
function abrirModal(editar = false, datos = null) {
    if (editar && datos) {
        document.getElementById('modalTitulo').textContent = 'Editar Mantenimiento';
        document.getElementById('mantenimientoId').value = datos.id;
        document.getElementById('unidad_id').value = datos.unidad_id;
        document.getElementById('fecha').value = new Date(datos.fecha).toISOString().slice(0, 16);
        document.getElementById('tipo').value = datos.tipo;
        document.getElementById('descripcion').value = datos.descripcion;
        document.getElementById('costo').value = datos.costo || '';
        document.getElementById('proveedor').value = datos.proveedor || '';
        document.getElementById('kilometraje').value = datos.kilometraje || '';
        
        if (datos.proximo_mantenimiento_km) {
            document.getElementById('proximo_mantenimiento_km').value = datos.proximo_mantenimiento_km;
        }
        
        if (datos.proximo_mantenimiento_fecha) {
            const fecha = new Date(datos.proximo_mantenimiento_fecha);
            document.getElementById('proximo_mantenimiento_fecha').value = fecha.toISOString().split('T')[0];
        }
    } else {
        // Establecer fecha y hora actual por defecto
        const now = new Date();
        const tzOffset = now.getTimezoneOffset() * 60000;
        const localISOTime = (new Date(now - tzOffset)).toISOString().slice(0, 16);
        document.getElementById('fecha').value = localISOTime;
    }
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

// Función para cerrar el modal
function cerrarModal() {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    formMantenimiento.reset();
    mantenimientoActualId = null;
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    // Event Listeners
    if (btnAgregar) {
        btnAgregar.addEventListener('click', function(e) {
            e.preventDefault();
            abrirModal();
        });
    }

    const btnCancelar = document.getElementById('cancelarMantenimiento');
    const btnCerrar = document.getElementById('cerrarModal');
    const btnCerrarConfirmacion = document.getElementById('cerrarConfirmacion');
    const btnCancelarEliminar = document.getElementById('cancelarEliminar');
    const btnConfirmarEliminar = document.getElementById('confirmarEliminar');
    
    if (btnCancelar) btnCancelar.addEventListener('click', cerrarModal);
    if (btnCerrar) btnCerrar.addEventListener('click', cerrarModal);
    
    // Cerrar al hacer clic fuera del modal
    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            cerrarModal();
        }
        if (e.target === modalConfirmacion) {
            modalConfirmacion.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });
    
    // Manejar envío del formulario
    if (formMantenimiento) {
        formMantenimiento.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(formMantenimiento);
            const mantenimientoId = document.getElementById('mantenimientoId').value;
            const url = mantenimientoId ? `/api/mantenimientos/${mantenimientoId}` : '/api/mantenimientos';
            const method = mantenimientoId ? 'PUT' : 'POST';
            
            fetch(url, {
                method: method,
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert('Error al guardar el mantenimiento: ' + (data.message || 'Error desconocido'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al guardar el mantenimiento');
            });
        });
    }
    
    // Manejar clic en botones de editar
    document.querySelectorAll('.btn-editar').forEach(btn => {
        btn.addEventListener('click', function() {
            const mantenimientoId = this.getAttribute('data-id');
            fetch(`/api/mantenimientos/${mantenimientoId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        abrirModal(true, data.data);
                    } else {
                        alert('Error al cargar el mantenimiento');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error al cargar el mantenimiento');
                });
        });
    });
    
    // Manejar clic en botones de eliminar
    document.querySelectorAll('.btn-eliminar').forEach(btn => {
        btn.addEventListener('click', function() {
            mantenimientoActualId = this.getAttribute('data-id');
            if (modalConfirmacion) {
                modalConfirmacion.style.display = 'block';
                document.body.style.overflow = 'hidden';
            }
        });
    });
    
    // Manejar confirmación de eliminación
    if (btnConfirmarEliminar) {
        btnConfirmarEliminar.addEventListener('click', function() {
            if (!mantenimientoActualId) return;
            
            fetch(`/api/mantenimientos/${mantenimientoActualId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert('Error al eliminar el mantenimiento: ' + (data.message || 'Error desconocido'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al eliminar el mantenimiento');
            })
            .finally(() => {
                if (modalConfirmacion) {
                    modalConfirmacion.style.display = 'none';
                    document.body.style.overflow = 'auto';
                }
            });
        });
    }
    
    // Cerrar modales
    if (btnCerrarConfirmacion) {
        btnCerrarConfirmacion.addEventListener('click', function() {
            if (modalConfirmacion) {
                modalConfirmacion.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    }
    
    if (btnCancelarEliminar) {
        btnCancelarEliminar.addEventListener('click', function() {
            if (modalConfirmacion) {
                modalConfirmacion.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    }
    
    // Aplicar filtros
    const btnFiltrar = document.getElementById('btnFiltrar');
    if (btnFiltrar) {
        btnFiltrar.addEventListener('click', function() {
            const unidadId = document.getElementById('filtroUnidad')?.value;
            const tipo = document.getElementById('filtroTipo')?.value;
            const fechaDesde = document.getElementById('filtroFechaDesde')?.value;
            const fechaHasta = document.getElementById('filtroFechaHasta')?.value;
            
            // Construir la URL con los parámetros de filtro
            let url = '/mantenimientos?';
            const params = new URLSearchParams();
            
            if (unidadId) params.append('unidad_id', unidadId);
            if (tipo) params.append('tipo', tipo);
            if (fechaDesde) params.append('fecha_desde', fechaDesde);
            if (fechaHasta) params.append('fecha_hasta', fechaHasta);
            
            window.location.href = url + params.toString();
        });
    }
    
    // Limpiar filtros
    const btnLimpiar = document.getElementById('btnLimpiar');
    if (btnLimpiar) {
        btnLimpiar.addEventListener('click', function() {
            window.location.href = '/mantenimientos';
        });
    }
    
    // Inicializar filtros desde la URL
    function inicializarFiltros() {
        const urlParams = new URLSearchParams(window.location.search);
        
        const unidadId = document.getElementById('filtroUnidad');
        const tipo = document.getElementById('filtroTipo');
        const fechaDesde = document.getElementById('filtroFechaDesde');
        const fechaHasta = document.getElementById('filtroFechaHasta');
        
        if (unidadId && urlParams.has('unidad_id')) {
            unidadId.value = urlParams.get('unidad_id');
        }
        if (tipo && urlParams.has('tipo')) {
            tipo.value = urlParams.get('tipo');
        }
        if (fechaDesde && urlParams.has('fecha_desde')) {
            fechaDesde.value = urlParams.get('fecha_desde');
        }
        if (fechaHasta && urlParams.has('fecha_hasta')) {
            fechaHasta.value = urlParams.get('fecha_hasta');
        }
    }
    
    // Inicializar la página
    inicializarFiltros();
});
