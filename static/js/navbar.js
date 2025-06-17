document.addEventListener('DOMContentLoaded', function() {
    // Add active class to current page link
    const currentLocation = location.href;
    const menuItems = document.querySelectorAll('.sidebar a');
    const menuLength = menuItems.length;

    for (let i = 0; i < menuLength; i++) {
        if (menuItems[i].href === currentLocation) {
            menuItems[i].parentElement.classList.add('active');
        }
    }
    
    // Add hover effect for sidebar items
    const navLinks = document.querySelectorAll('.sidebar a');
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.parentElement.classList.add('hover');
        });
        link.addEventListener('mouseleave', function() {
            this.parentElement.classList.remove('hover');
        });
    });
});