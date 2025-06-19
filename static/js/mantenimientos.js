// Variables globales
let mantenimientoActualId = null; // Used for delete confirmation and potentially for file uploads if modal is open
const modal = document.getElementById('modalMantenimiento');
const modalConfirmacion = document.getElementById('modalConfirmarEliminar');
const formMantenimiento = document.getElementById('formMantenimiento');
const btnAgregar = document.getElementById('btnAgregarMantenimiento');
const btnGuardar = document.getElementById('btnGuardar');

// Función para abrir el modal de mantenimiento
function abrirModal(editar = false, datos = null, readOnly = false) {
    const modalTitulo = document.getElementById('modalTitulo');
    formMantenimiento.reset(); // Reset form first

    // Clear dynamic content areas
    document.getElementById('trabajos_realizados_detalle').value = '';
    document.getElementById('mantenimiento_archivos_input').value = '';
    document.getElementById('archivos_adjuntos_list').innerHTML = '';
    document.getElementById('archivos_adjuntos_list_container').style.display = 'none';

    const formElements = formMantenimiento.elements;

    if (editar && datos) { // Handles both Edit and View modes for data population
        document.getElementById('mantenimientoId').value = datos.id;
        mantenimientoActualId = datos.id; // Set for potential file operations while modal is open
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
        document.getElementById('trabajos_realizados_detalle').value = datos.trabajos_realizados_detalle || '';

        cargarArchivosAdjuntos(datos.id); // Load existing files

    } else { // Modo nuevo
        mantenimientoActualId = null; // Clear any previous ID for new entries
        document.getElementById('mantenimientoId').value = ''; // Important for new entries
        document.getElementById('fecha').value = new Date().toISOString().split('T')[0];
        // Default values for new form
        document.getElementById('unidad').value = '';
        document.getElementById('tipo').value = 'preventivo';
        document.getElementById('kilometraje').value = '';
        document.getElementById('proximo').value = '';
        document.getElementById('descripcion').value = '';
        document.getElementById('proveedor').value = '';
        document.getElementById('costo').value = '';
        document.getElementById('observaciones').value = '';
        document.getElementById('completado').checked = false;
        document.getElementById('trabajos_realizados_detalle').value = '';
    }

    // Set modal title and field states
    if (readOnly) {
        modalTitulo.textContent = 'Ver Mantenimiento';
        for (let i = 0; i < formElements.length; i++) {
            formElements[i].disabled = true;
        }
        document.getElementById('mantenimiento_archivos_input').disabled = true; // Also disable file input
        if(btnGuardar) btnGuardar.style.display = 'none';
    } else { // New or Edit mode
        modalTitulo.textContent = editar ? 'Editar Mantenimiento' : 'Nuevo Mantenimiento';
        for (let i = 0; i < formElements.length; i++) {
            formElements[i].disabled = false;
        }
        document.getElementById('mantenimiento_archivos_input').disabled = false;
        if(btnGuardar) btnGuardar.style.display = 'inline-block';
    }

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// Función para cerrar el modal
function cerrarModal() {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    formMantenimiento.reset(); // Resets to initial HTML state
    // Explicitly clear dynamic content not reset by form.reset()
    document.getElementById('trabajos_realizados_detalle').value = '';
    document.getElementById('mantenimiento_archivos_input').value = '';
    document.getElementById('archivos_adjuntos_list').innerHTML = '';
    document.getElementById('archivos_adjuntos_list_container').style.display = 'none';
    mantenimientoActualId = null; // Clear current ID

    const formElements = formMantenimiento.elements;
    for (let i = 0; i < formElements.length; i++) {
        formElements[i].disabled = false;
    }
    if(btnGuardar) btnGuardar.style.display = 'inline-block';
}

// Función para ver los detalles de un mantenimiento (already updated in previous step)
function verMantenimiento(id) {
    fetch(`/api/mantenimientos/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                abrirModal(true, data.data, true);
            } else {
                Swal.fire('Error', `Error al cargar el mantenimiento para ver: ${data.message || 'No se encontraron datos.'}`, 'error');
            }
        })
        .catch(error => {
            console.error('Error en verMantenimiento:', error);
            Swal.fire('Error de Red', 'No se pudo conectar para cargar los detalles.', 'error');
        });
}

// Function to load and display attached files
function cargarArchivosAdjuntos(mantenimientoId) {
    if (!mantenimientoId) return;

    fetch(`/api/mantenimientos/${mantenimientoId}/archivos`)
        .then(response => response.json())
        .then(data => {
            const listElement = document.getElementById('archivos_adjuntos_list');
            const container = document.getElementById('archivos_adjuntos_list_container');
            listElement.innerHTML = '';

            if (data.success && data.archivos && data.archivos.length > 0) {
                data.archivos.forEach(archivo => {
                    const listItem = document.createElement('li');
                    listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
                    // Check if the current user is allowed to delete (readOnly flag of the modal can be a proxy)
                    const deleteButtonDisabled = document.getElementById('trabajos_realizados_detalle').disabled; // If detail field is disabled, modal is likely readOnly

                    listItem.innerHTML = `
                        <a href="/api/archivos/${archivo.id}" target="_blank">${archivo.nombre_archivo}</a>
                        <button type="button" class="btn btn-sm btn-danger btn-eliminar-archivo"
                                data-archivo-id="${archivo.id}" title="Eliminar archivo" ${deleteButtonDisabled ? 'disabled' : ''}>&times;</button>
                    `;
                    listElement.appendChild(listItem);
                });
                container.style.display = 'block';
            } else {
                container.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error al cargar archivos adjuntos:', error);
            // Optionally show a user-facing error message here
        });
}

// Function to delete an attached file
function eliminarArchivo(archivoId, botonElemento) {
    Swal.fire({
        title: '¿Eliminar Archivo?',
        text: "Esta acción no se puede deshacer.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/api/archivos/${archivoId}`, { method: 'DELETE' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire('Eliminado', 'El archivo ha sido eliminado.', 'success');
                        if (botonElemento) {
                            const listItem = botonElemento.closest('li.list-group-item');
                            if (listItem) listItem.remove();

                            const listElement = document.getElementById('archivos_adjuntos_list');
                            if (!listElement.hasChildNodes()) {
                                document.getElementById('archivos_adjuntos_list_container').style.display = 'none';
                            }
                        }
                    } else {
                        Swal.fire('Error', data.message || 'No se pudo eliminar el archivo.', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error de red al eliminar archivo:', error);
                    Swal.fire('Error de Red', 'No se pudo conectar para eliminar el archivo.', 'error');
                });
        }
    });
}


// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    if (typeof $ === 'function') { // Check if jQuery is loaded for tooltips
        $('[data-toggle="tooltip"]').tooltip();
    }
    inicializarFiltros();

    if (btnAgregar) {
        btnAgregar.addEventListener('click', function(e) {
            e.preventDefault();
            abrirModal(false, null, false);
        });
    }

    const cerrarModalSpan = document.getElementById('cerrarModal');
    if (cerrarModalSpan) cerrarModalSpan.addEventListener('click', cerrarModal);

    const btnCancelar = document.getElementById('btnCancelar');
    if (btnCancelar) btnCancelar.addEventListener('click', cerrarModal);
    
    window.addEventListener('click', function(event) {
        if (event.target === modal) cerrarModal();
        if (event.target === modalConfirmacion) {
            modalConfirmacion.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });
    
    // Main form submission
    if (formMantenimiento) {
        formMantenimiento.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const currentMantenimientoId = document.getElementById('mantenimientoId').value;
            const formData = new FormData(formMantenimiento); // 'this' is the form
            // 'trabajos_realizados_detalle' is already part of FormData due to name attribute
            // Ensure 'completado' is correctly set as it might not be if unchecked
            formData.set('completado', document.getElementById('completado').checked.toString());

            const url = currentMantenimientoId ? `/api/mantenimientos/${currentMantenimientoId}` : '/api/mantenimientos';
            const method = currentMantenimientoId ? 'PUT' : 'POST';

            fetch(url, { method: method, body: formData })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const savedMantenimientoId = data.mantenimiento_id || currentMantenimientoId;
                    const filesInput = document.getElementById('mantenimiento_archivos_input');
                    const files = filesInput.files;

                    if (files.length > 0 && savedMantenimientoId) {
                        const uploadPromises = [];
                        for (const file of files) {
                            const fileFormData = new FormData();
                            fileFormData.append('file', file);

                            uploadPromises.push(
                                fetch(`/api/mantenimientos/${savedMantenimientoId}/archivos`, {
                                    method: 'POST',
                                    body: fileFormData
                                })
                                .then(response => response.json())
                                .then(fileData => {
                                    if (!fileData.success) console.warn('Error al subir archivo:', fileData.message);
                                    return fileData.success;
                                })
                                .catch(error => {
                                    console.error('Error de red al subir archivo:', error);
                                    return false;
                                })
                            );
                        }

                        Promise.all(uploadPromises).then(results => {
                            const allSuccessful = results.every(r => r === true);
                            filesInput.value = ''; // Clear file input
                            if (allSuccessful) {
                                Swal.fire('¡Éxito!', 'Mantenimiento y archivos guardados.', 'success').then(() => window.location.reload());
                            } else {
                                Swal.fire('Parcialmente Completo', 'Se guardó el mantenimiento, pero algunos archivos no pudieron subirse.', 'warning').then(() => window.location.reload());
                            }
                        });
                    } else {
                        // No files, or no ID (should not happen if main save was success)
                        Swal.fire('¡Éxito!', data.message || 'Mantenimiento guardado.', 'success').then(() => window.location.reload());
                    }
                } else {
                    Swal.fire('Error', data.message || 'No se pudo guardar el mantenimiento.', 'error');
                }
            })
            .catch(error => {
                console.error('Error en submit formMantenimiento:', error);
                Swal.fire('Error de Red', 'No se pudo conectar para guardar el mantenimiento.', 'error');
            });
        });
    }
    
    // Event listeners for action buttons in table
    document.querySelectorAll('.btn-ver').forEach(btn => {
        btn.addEventListener('click', function() { verMantenimiento(this.getAttribute('data-id')); });
    });

    document.querySelectorAll('.btn-editar').forEach(btn => {
        btn.addEventListener('click', function() {
            const mantenimientoId = this.getAttribute('data-id');
            fetch(`/api/mantenimientos/${mantenimientoId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.data) {
                        abrirModal(true, data.data, false);
                    } else {
                        Swal.fire('Error', `Error al cargar el mantenimiento para editar: ${data.message || 'No se encontraron datos.'}`, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error en btn-editar fetch:', error);
                    Swal.fire('Error de Red', 'No se pudo conectar para cargar los datos de edición.', 'error');
                });
        });
    });
    
    document.querySelectorAll('.btn-eliminar').forEach(btn => {
        btn.addEventListener('click', function() {
            mantenimientoActualId = this.getAttribute('data-id'); // For delete confirmation
            if (modalConfirmacion) {
                modalConfirmacion.style.display = 'flex';
                document.body.style.overflow = 'hidden';
            }
        });
    });
    
    // Delete confirmation
    const btnConfirmarEliminar = document.getElementById('btnConfirmarEliminar');
    if (btnConfirmarEliminar) {
        btnConfirmarEliminar.addEventListener('click', function() {
            if (!mantenimientoActualId) return;
            fetch(`/api/mantenimientos/${mantenimientoActualId}`, { method: 'DELETE' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload(); // Success implies data is gone
                } else {
                    Swal.fire('Error', `Error al eliminar el mantenimiento: ${data.message || 'Error desconocido'}`, 'error');
                }
            })
            .catch(error => {
                console.error('Error en btnConfirmarEliminar fetch:', error);
                Swal.fire('Error de Red', 'No se pudo conectar para eliminar el mantenimiento.', 'error');
            })
            .finally(() => {
                if (modalConfirmacion) modalConfirmacion.style.display = 'none';
                document.body.style.overflow = 'auto';
                mantenimientoActualId = null;
            });
        });
    }
    
    // Event listener for deleting attached files (delegated from list container)
    const archivosListElement = document.getElementById('archivos_adjuntos_list');
    if (archivosListElement) {
        archivosListElement.addEventListener('click', function(event) {
            const button = event.target.closest('.btn-eliminar-archivo');
            if (button) {
                const archivoId = button.getAttribute('data-archivo-id');
                if (archivoId) {
                    eliminarArchivo(archivoId, button);
                }
            }
        });
    }

    // Close buttons for delete confirmation modal
    const modalConfirmarEliminar_closeButton = modalConfirmacion ? modalConfirmacion.querySelector('.close') : null;
    if (modalConfirmarEliminar_closeButton) {
        modalConfirmarEliminar_closeButton.addEventListener('click', () => {
            if (modalConfirmacion) modalConfirmacion.style.display = 'none';
            document.body.style.overflow = 'auto';
        });
    }
    const modalConfirmarEliminar_cancelButton = modalConfirmacion ? modalConfirmacion.querySelector('.btn-secondary[data-dismiss="modal"]') : null;
    if (modalConfirmarEliminar_cancelButton) {
         modalConfirmarEliminar_cancelButton.addEventListener('click', () => {
            if (modalConfirmacion) modalConfirmacion.style.display = 'none';
            document.body.style.overflow = 'auto';
        });
    }

    // Filter buttons
    const btnFiltrar = document.getElementById('btnFiltrar');
    if (btnFiltrar) {
        btnFiltrar.addEventListener('click', function() {
            const unidadId = document.getElementById('filtroUnidad')?.value;
            const tipo = document.getElementById('filtroTipo')?.value;
            const fechaDesde = document.getElementById('filtroFechaDesde')?.value;
            const fechaHasta = document.getElementById('filtroFechaHasta')?.value;
            
            const params = new URLSearchParams();
            if (unidadId) params.append('unidad_id', unidadId);
            if (tipo) params.append('tipo', tipo);
            if (fechaDesde) params.append('fecha_desde', fechaDesde);
            if (fechaHasta) params.append('fecha_hasta', fechaHasta);
            
            window.location.href = `/mantenimientos?${params.toString()}`;
        });
    }
    
    const btnLimpiar = document.getElementById('btnLimpiar');
    if (btnLimpiar) {
        btnLimpiar.addEventListener('click', function() {
            window.location.href = '/mantenimientos';
        });
    }
    
    // Function to initialize filters from URL (already defined and seems fine)
    function inicializarFiltros() {
        const urlParams = new URLSearchParams(window.location.search);
        const filtroUnidadEl = document.getElementById('filtroUnidad');
        const filtroTipoEl = document.getElementById('filtroTipo');
        const filtroFechaDesdeEl = document.getElementById('filtroFechaDesde');
        const filtroFechaHastaEl = document.getElementById('filtroFechaHasta');
        
        if (filtroUnidadEl && urlParams.has('unidad_id')) filtroUnidadEl.value = urlParams.get('unidad_id');
        if (filtroTipoEl && urlParams.has('tipo')) filtroTipoEl.value = urlParams.get('tipo');
        if (filtroFechaDesdeEl && urlParams.has('fecha_desde')) filtroFechaDesdeEl.value = urlParams.get('fecha_desde');
        if (filtroFechaHastaEl && urlParams.has('fecha_hasta')) filtroFechaHastaEl.value = urlParams.get('fecha_hasta');
    }
});
