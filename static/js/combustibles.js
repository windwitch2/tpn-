// Funcionalidad para la vista de Combustibles
document.addEventListener('DOMContentLoaded', function() {
    // Inicialización de componentes o funcionalidades específicas
    console.log('Combustibles cargado correctamente');
    
    // Ejemplo de funcionalidad: Resaltar filas al pasar el mouse
    const filas = document.querySelectorAll('tbody tr');
    filas.forEach(fila => {
        fila.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });
        
        fila.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
    
    // Aquí puedes agregar más funcionalidades según sea necesario
});
