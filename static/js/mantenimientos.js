// Variables globales
let mantenimientoActualId = null;
const modal = document.getElementById('modalMantenimiento');
const modalConfirmacion = document.getElementById('modalConfirmarEliminar');
const formMantenimiento = document.getElementById('formMantenimiento');
const btnAgregar = document.getElementById('btnAgregarMantenimiento');
const btnGuardar = document.getElementById('btnGuardar'); // Get the Guardar button

// Función para abrir el modal de mantenimiento
function abrirModal(editar = false, datos = null, readOnly = false) {
    const modalTitulo = document.getElementById('modalTitulo');
    formMantenimiento.reset(); // Reset form first

    // Get all form elements
    const formElements = formMantenimiento.elements;

    if (editar && datos) { // Handles both Edit and View modes for data population
        document.getElementById('mantenimientoId').value = datos.id;
        document.getElementById('unidad').value = datos.unidad_id;
        document.getElementById('tipo').value = datos.tipo;
        if (datos.fecha) {
            let fechaToSet = datos.fecha;
            if (datos.fecha.includes('T')) {
                 fechaToSet = datos.fecha.split('T')[0];
            }
            document.getElementById('fecha').value = fechaToSet;
        }
        document.getElementById('kilometraje').value = datos.kilometraje || '';
        document.getElementById('proximo').value = datos.proximo_kilometraje || '';
        document.getElementById('descripcion').value = datos.descripcion;
        document.getElementById('proveedor').value = datos.proveedor || '';
        document.getElementById('costo').value = datos.costo || '';
        document.getElementById('observaciones').value = datos.observaciones || '';
        document.getElementById('completado').checked = datos.completado || false;
    } else { // Modo nuevo
        modalTitulo.textContent = 'Nuevo Mantenimiento';
        document.getElementById('fecha').value = new Date().toISOString().split('T')[0];
        document.getElementById('mantenimientoId').value = '';
        document.getElementById('unidad').value = '';
        document.getElementById('tipo').value = 'preventivo';
        document.getElementById('kilometraje').value = '';
        document.getElementById('proximo').value = '';
        document.getElementById('descripcion').value = '';
        document.getElementById('proveedor').value = '';
        document.getElementById('costo').value = '';
        document.getElementById('observaciones').value = '';
        document.getElementById('completado').checked = false;
    }

    if (readOnly) {
        modalTitulo.textContent = 'Ver Mantenimiento';
        for (let i = 0; i < formElements.length; i++) {
            formElements[i].disabled = true;
        }
        if(btnGuardar) btnGuardar.style.display = 'none';
    } else if (editar) { // Edit mode (not readOnly)
        modalTitulo.textContent = 'Editar Mantenimiento';
        for (let i = 0; i < formElements.length; i++) {
            formElements[i].disabled = false;
        }
        if(btnGuardar) btnGuardar.style.display = 'inline-block'; // or 'block' depending on original style
    } else { // New mode (not readOnly, not edit)
         modalTitulo.textContent = 'Nuevo Mantenimiento';
        for (let i = 0; i < formElements.length; i++) {
            formElements[i].disabled = false;
        }
        if(btnGuardar) btnGuardar.style.display = 'inline-block';
    }

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// Función para cerrar el modal
function cerrarModal() {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    formMantenimiento.reset();
    // Re-enable form elements and show Guardar button for next time
    const formElements = formMantenimiento.elements;
    for (let i = 0; i < formElements.length; i++) {
        formElements[i].disabled = false;
    }
    if(btnGuardar) btnGuardar.style.display = 'inline-block';
}

// Función para ver los detalles de un mantenimiento
function verMantenimiento(id) {
    fetch(`/api/mantenimientos/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                abrirModal(true, data.data, true); // editar=true to populate, data=data.data, readOnly=true
            } else {
                Swal.fire({
                    title: 'Error',
                    text: 'Error al cargar el mantenimiento para ver: ' + (data.message || 'No se encontraron datos.'),
                    icon: 'error',
                    confirmButtonText: 'Aceptar'
                });
            }
        })
        .catch(error => {
            console.error('Error en verMantenimiento:', error);
            Swal.fire({
                title: 'Error de Red',
                text: 'No se pudo conectar al servidor para cargar los detalles del mantenimiento.',
                icon: 'error',
                confirmButtonText: 'Aceptar'
            });
        });
}


// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    if (typeof $ === 'function') {
        $('[data-toggle="tooltip"]').tooltip();
    }
    inicializarFiltros();

    if (btnAgregar) {
        btnAgregar.addEventListener('click', function(e) {
            e.preventDefault();
            abrirModal(false, null, false); // Nuevo: editar=false, datos=null, readOnly=false
        });
    }

    const cerrarModalSpan = document.getElementById('cerrarModal');
    if (cerrarModalSpan) {
        cerrarModalSpan.addEventListener('click', cerrarModal);
    }

    const btnCancelar = document.getElementById('btnCancelar');
    if (btnCancelar) {
        btnCancelar.addEventListener('click', cerrarModal);
    }
    
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            cerrarModal();
        }
        if (event.target === modalConfirmacion) {
            modalConfirmacion.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });
    
    if (formMantenimiento) {
        formMantenimiento.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(formMantenimiento);
            const mantenimientoId = document.getElementById('mantenimientoId').value;
            const url = mantenimientoId ? `/api/mantenimientos/${mantenimientoId}` : '/api/mantenimientos';
            const method = mantenimientoId ? 'PUT' : 'POST';
            
            // Ensure 'completado' is true/false not 'on'/null
            formData.set('completado', document.getElementById('completado').checked);

            fetch(url, {
                method: method,
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        title: '¡Éxito!',
                        text: 'El mantenimiento ha sido guardado correctamente.',
                        icon: 'success',
                        confirmButtonText: 'Aceptar'
                    }).then(() => {
                        cerrarModal();
                        window.location.reload();
                    });
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: 'Error al guardar el mantenimiento: ' + (data.message || data.error || 'Error desconocido'),
                        icon: 'error',
                        confirmButtonText: 'Aceptar'
                    });
                }
            })
            .catch(error => {
                console.error('Error en submit formMantenimiento:', error);
                Swal.fire({
                    title: 'Error de Red',
                    text: 'No se pudo conectar al servidor para guardar el mantenimiento.',
                    icon: 'error',
                    confirmButtonText: 'Aceptar'
                });
            });
        });
    }
    
    document.querySelectorAll('.btn-ver').forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            verMantenimiento(id);
        });
    });

    document.querySelectorAll('.btn-editar').forEach(btn => {
        btn.addEventListener('click', function() {
            const mantenimientoId = this.getAttribute('data-id');
            fetch(`/api/mantenimientos/${mantenimientoId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.data) {
                        abrirModal(true, data.data, false); // Editar: editar=true, datos=data.data, readOnly=false
                    } else {
                        Swal.fire({
                            title: 'Error',
                            text: 'Error al cargar el mantenimiento para editar: ' + (data.message || 'No se encontraron datos.'),
                            icon: 'error',
                            confirmButtonText: 'Aceptar'
                        });
                    }
                })
                .catch(error => {
                    console.error('Error en btn-editar fetch:', error);
                    Swal.fire({
                        title: 'Error de Red',
                        text: 'No se pudo conectar al servidor para cargar los datos de edición.',
                        icon: 'error',
                        confirmButtonText: 'Aceptar'
                    });
                });
        });
    });
    
    document.querySelectorAll('.btn-eliminar').forEach(btn => {
        btn.addEventListener('click', function() {
            mantenimientoActualId = this.getAttribute('data-id');
            if (modalConfirmacion) {
                modalConfirmacion.style.display = 'flex';
                document.body.style.overflow = 'hidden';
            }
        });
    });
    
    const btnConfirmarEliminar = document.getElementById('btnConfirmarEliminar');
    if (btnConfirmarEliminar) {
        btnConfirmarEliminar.addEventListener('click', function() {
            if (!mantenimientoActualId) return;
            
            fetch(`/api/mantenimientos/${mantenimientoActualId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // No specific Swal, reload will show updated table
                    window.location.reload();
                } else {
                     Swal.fire({
                        title: 'Error',
                        text: 'Error al eliminar el mantenimiento: ' + (data.message || data.error || 'Error desconocido'),
                        icon: 'error',
                        confirmButtonText: 'Aceptar'
                    });
                }
            })
            .catch(error => {
                console.error('Error en btnConfirmarEliminar fetch:', error);
                Swal.fire({
                    title: 'Error de Red',
                    text: 'No se pudo conectar al servidor para eliminar el mantenimiento.',
                    icon: 'error',
                    confirmButtonText: 'Aceptar'
                });
            })
            .finally(() => {
                if (modalConfirmacion) {
                    modalConfirmacion.style.display = 'none';
                    document.body.style.overflow = 'auto';
                }
                mantenimientoActualId = null;
            });
        });
    }
    
    const modalConfirmarEliminar_closeButton = modalConfirmacion ? modalConfirmacion.querySelector('.close') : null;
    if (modalConfirmarEliminar_closeButton) {
        modalConfirmarEliminar_closeButton.addEventListener('click', () => {
            modalConfirmacion.style.display = 'none';
            document.body.style.overflow = 'auto';
        });
    }
    const modalConfirmarEliminar_cancelButton = modalConfirmacion ? modalConfirmacion.querySelector('.btn-secondary[data-dismiss="modal"]') : null;
    if (modalConfirmarEliminar_cancelButton) {
         modalConfirmarEliminar_cancelButton.addEventListener('click', () => {
            modalConfirmacion.style.display = 'none';
            document.body.style.overflow = 'auto';
        });
    }

    const btnFiltrar = document.getElementById('btnFiltrar');
    if (btnFiltrar) {
        btnFiltrar.addEventListener('click', function() {
            const unidadId = document.getElementById('filtroUnidad')?.value;
            const tipo = document.getElementById('filtroTipo')?.value;
            const fechaDesde = document.getElementById('filtroFechaDesde')?.value;
            const fechaHasta = document.getElementById('filtroFechaHasta')?.value;
            
            let url = '/mantenimientos?';
            const params = new URLSearchParams();
            
            if (unidadId) params.append('unidad_id', unidadId);
            if (tipo) params.append('tipo', tipo);
            if (fechaDesde) params.append('fecha_desde', fechaDesde);
            if (fechaHasta) params.append('fecha_hasta', fechaHasta);
            
            window.location.href = url + params.toString();
        });
    }
    
    const btnLimpiar = document.getElementById('btnLimpiar');
    if (btnLimpiar) {
        btnLimpiar.addEventListener('click', function() {
            window.location.href = '/mantenimientos';
        });
    }
    
    function inicializarFiltros() {
        const urlParams = new URLSearchParams(window.location.search);
        
        const filtroUnidadEl = document.getElementById('filtroUnidad');
        const filtroTipoEl = document.getElementById('filtroTipo');
        const filtroFechaDesdeEl = document.getElementById('filtroFechaDesde');
        const filtroFechaHastaEl = document.getElementById('filtroFechaHasta');
        
        if (filtroUnidadEl && urlParams.has('unidad_id')) {
            filtroUnidadEl.value = urlParams.get('unidad_id');
        }
        if (filtroTipoEl && urlParams.has('tipo')) {
            filtroTipoEl.value = urlParams.get('tipo');
        }
        if (filtroFechaDesdeEl && urlParams.has('fecha_desde')) {
            filtroFechaDesdeEl.value = urlParams.get('fecha_desde');
        }
        if (filtroFechaHastaEl && urlParams.has('fecha_hasta')) {
            filtroFechaHastaEl.value = urlParams.get('fecha_hasta');
        }
    }
});
