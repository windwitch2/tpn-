// Global variable to track the selected unit ID
let unidadSeleccionadaId = null;

// Show notification using SweetAlert2 or fallback to alert
function showAlert(message, type = 'info') {
    if (typeof Swal !== 'undefined') {
        const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer);
                toast.addEventListener('mouseleave', Swal.resumeTimer);
            }
        });
        
        Toast.fire({
            icon: type,
            title: message
        });
    } else {
        alert(message);
    }
}

// Function to update the summary counters
function actualizarContadores() {
    const contadores = {
        total: 0,
        funcionales: 0,
        en_reparacion: 0,
        sin_reparacion: 0
    };
    
    // Count units by status
    document.querySelectorAll('.estado-badge').forEach(badge => {
        contadores.total++;
        const estado = badge.textContent.trim();
        
        if (estado === 'Funcional') {
            contadores.funcionales++;
        } else if (estado === 'En Reparación') {
            contadores.en_reparacion++;
        } else if (estado === 'Sin Reparación') {
            contadores.sin_reparacion++;
        }
    });
    
    // Update the UI
    const resumenElement = document.getElementById('resumen');
    if (resumenElement) {
        const totalElement = resumenElement.querySelector('.resumen-item:first-child .resumen-valor');
        const funcionalesElement = resumenElement.querySelector('.estado-card:nth-child(2) .resumen-valor');
        const enReparacionElement = resumenElement.querySelector('.estado-card:nth-child(3) .resumen-valor');
        const sinReparacionElement = resumenElement.querySelector('.estado-card:last-child .resumen-valor');
        
        if (totalElement) totalElement.textContent = contadores.total;
        if (funcionalesElement) funcionalesElement.textContent = contadores.funcionales;
        if (enReparacionElement) enReparacionElement.textContent = contadores.en_reparacion;
        if (sinReparacionElement) sinReparacionElement.textContent = contadores.sin_reparacion;
    }
}

// Delete unit with confirmation
async function eliminarUnidad(unidadId) {
    const confirmResult = await Swal.fire({
        title: '¿Estás seguro?',
        text: 'Esta acción eliminará la unidad y no se podrá deshacer',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar',
        reverseButtons: true
    });

    if (!confirmResult.isConfirmed) return;

    try {
        const response = await fetch(`/eliminar_unidad/${unidadId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Remove the row from the table
            const row = document.querySelector(`tr[data-unidad-id="${unidadId}"]`);
            if (row) {
                row.remove();
                showAlert('Unidad eliminada correctamente', 'success');
                actualizarContadores();
            }
        } else {
            throw new Error(data.error || 'Error al eliminar la unidad');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Error al eliminar la unidad: ' + error.message, 'error');
    }
}

// Initialize the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Create and configure the floating action button (FAB)
    const floatingBtn = document.createElement('button');
    floatingBtn.className = 'btn btn-primario floating-btn';
    floatingBtn.id = 'floatingAgregar';
    floatingBtn.setAttribute('aria-label', 'Agregar nueva unidad');
    floatingBtn.innerHTML = '<i class="fas fa-plus me-2"></i><span class="d-none d-sm-inline">Agregar Unidad</span>';
    document.body.appendChild(floatingBtn);

    // Set up event delegation for delete buttons
    document.addEventListener('click', function(e) {
        const deleteBtn = e.target.closest('.eliminar-unidad');
        if (deleteBtn) {
            e.preventDefault();
            const unidadId = deleteBtn.getAttribute('data-id');
            if (unidadId) {
                eliminarUnidad(unidadId);
            }
        }
    });

    // Set up the unit modal
    const modal = document.getElementById('modalUnidad');
    const abrirModalBtn = document.getElementById('abrirModal');
    
    // Configure the floating button to open the modal
    if (floatingBtn && modal) {
        floatingBtn.addEventListener('click', (e) => {
            e.preventDefault();
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
            // Focus on the first input field when modal opens
            const firstInput = modal.querySelector('input, select, textarea');
            if (firstInput) firstInput.focus();
        });
    }
    }

    // Set up IntersectionObserver to show/hide floating button based on main button visibility
    if (abrirModalBtn) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (floatingBtn) {
                    floatingBtn.style.display = entry.isIntersecting ? 'none' : 'flex';
                }
            });
        }, {threshold: 0.1});

        observer.observe(abrirModalBtn);
    }

    // Set up search functionality
    const buscador = document.getElementById('buscadorUnidades');
    if (buscador) {
        buscador.addEventListener('input', function() {
            const searchTerm = this.value.trim().toLowerCase();
            const rows = document.querySelectorAll('#tablaUnidades tbody tr');
            let visibleCount = 0;
            
            rows.forEach(row => {
                const rowText = row.textContent.toLowerCase();
                const isVisible = rowText.includes(searchTerm);
                row.style.display = isVisible ? '' : 'none';
                if (isVisible) visibleCount++;
            });

            // Show a message if no results are found
            const noResults = document.getElementById('noResults');
            if (!noResults && visibleCount === 0 && searchTerm !== '') {
                const tbody = document.querySelector('#tablaUnidades tbody');
                const tr = document.createElement('tr');
                tr.id = 'noResults';
                tr.innerHTML = `<td colspan="10" class="text-center py-4">No se encontraron unidades que coincidan con "${searchTerm}"</td>`;
                tbody.appendChild(tr);
            } else if (noResults && (visibleCount > 0 || searchTerm === '')) {
                noResults.remove();
            }
        });
    }

    // Handle unit form submission
    const formAgregarUnidad = document.getElementById('formAgregarUnidad');
    if (formAgregarUnidad) {
        formAgregarUnidad.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            
            // Disable button and show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Guardando...';
            
            try {
                const response = await fetch('/agregar_unidad', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(Object.fromEntries(formData))
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showAlert('Unidad agregada correctamente', 'success');
                    // Reset form and close modal
                    this.reset();
                    const modal = this.closest('.modal');
                    if (modal) modal.style.display = 'none';
                    
                    // Reload the page to show the new unit
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    throw new Error(data.error || 'Error al agregar la unidad');
                }
            } catch (error) {
                console.error('Error:', error);
                showAlert('Error al agregar la unidad: ' + error.message, 'error');
            } finally {
                // Restore button state
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
        });
    }

    // Handle modal close buttons
    const cerrarModal = document.getElementById('cerrarModal');
    const cerrarModal2 = document.getElementById('cerrarModal2');
    
    [cerrarModal, cerrarModal2].forEach(btn => {
        if (btn) {
            btn.addEventListener('click', () => {
                const modal = document.getElementById('modalUnidad');
                if (modal) {
                    modal.style.display = 'none';
                    document.body.style.overflow = 'auto';
                }
            });
        }
    });

    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('modalUnidad');
        if (e.target === modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const modal = document.getElementById('modalUnidad');
            if (modal && modal.style.display === 'block') {
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        }
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Update counters on page load
    actualizarContadores();
});
