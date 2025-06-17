/**
 * Status Modals - Handles the status-related modals functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize color picker preview
    const colorPicker = document.getElementById('colorNuevoEstado');
    const colorPreview = document.getElementById('colorPreview');
    
    if (colorPicker && colorPreview) {
        // Update preview when color changes
        colorPicker.addEventListener('input', function() {
            colorPreview.style.backgroundColor = this.value;
        });
    }
});

// Show modal to add new status
function mostrarModalNuevoEstado() {
    // Reset form
    document.getElementById('nombreNuevoEstado').value = '';
    document.getElementById('colorNuevoEstado').value = '#4e73df';
    document.getElementById('colorPreview').style.backgroundColor = '#4e73df';
    
    // Show modal
    document.getElementById('modalNuevoEstado').style.display = 'block';
}

// Add new status
async function agregarNuevoEstado() {
    const nombre = document.getElementById('nombreNuevoEstado').value.trim();
    const color = document.getElementById('colorNuevoEstado').value;
    
    if (!nombre) {
        showAlert('Por favor ingresa un nombre para el estado', 'error');
        return;
    }
    
    try {
        const response = await fetch('/agregar_estado', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                nombre: nombre,
                color: color
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Close modal
            cerrarModal('modalNuevoEstado');
            
            // Show success message
            showAlert('Estado agregado correctamente', 'success');
            
            // Reload the page to show the new status
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert(data.error || 'Error al agregar el estado', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Error al conectar con el servidor', 'error');
    }
}

// Show status selector modal
function mostrarSelectorEstado(element, estadoActual) {
    const unidadId = element.getAttribute('data-unidad-id');
    const modal = document.getElementById('modalCambiarEstado');
    const select = document.getElementById('nuevoEstadoSelect');
    
    // Store the unit ID in the modal for later use
    modal.setAttribute('data-unidad-id', unidadId);
    
    // Set the current status as selected
    if (select) {
        for (let i = 0; i < select.options.length; i++) {
            if (select.options[i].value === estadoActual) {
                select.selectedIndex = i;
                break;
            }
        }
    }
    
    // Show the modal
    modal.style.display = 'block';
}

// Update status
async function actualizarEstado() {
    const modal = document.getElementById('modalCambiarEstado');
    const unidadId = modal.getAttribute('data-unidad-id');
    const select = document.getElementById('nuevoEstadoSelect');
    const nuevoEstado = select.value;
    const nuevoColor = select.options[select.selectedIndex].getAttribute('data-color');
    
    if (!unidadId || !nuevoEstado) {
        showAlert('Error: Datos incompletos', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/actualizar_estado/${unidadId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                estado: nuevoEstado,
                color: nuevoColor
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update the status badge in the UI
            const badge = document.querySelector(`[data-unidad-id="${unidadId}"] .estado-badge`);
            if (badge) {
                badge.textContent = nuevoEstado;
                badge.style.backgroundColor = nuevoColor;
            }
            
            // Close the modal
            cerrarModal('modalCambiarEstado');
            
            // Show success message
            showAlert('Estado actualizado correctamente', 'success');
            
            // Reload the page to update the summary
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert(data.error || 'Error al actualizar el estado', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Error al conectar con el servidor', 'error');
    }
}

// Close modal
function cerrarModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Show alert message
function showAlert(message, type = 'info') {
    // Use SweetAlert2 if available, otherwise fallback to alert
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

// Close modals when clicking outside
window.onclick = function(event) {
    const modals = document.getElementsByClassName('modal');
    for (let modal of modals) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    }
};

// Close modals with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modals = document.getElementsByClassName('modal');
        for (let modal of modals) {
            modal.style.display = 'none';
        }
    }
});
