document.addEventListener('DOMContentLoaded', () => {
    const menuToggle = document.getElementById('menuToggle');
    const closeSidebar = document.getElementById('closeSidebar');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    const toggleSidebar = () => {
        sidebar.classList.toggle('-translate-x-full');
        overlay.classList.toggle('hidden');
    };

    menuToggle?.addEventListener('click', toggleSidebar);
    closeSidebar?.addEventListener('click', toggleSidebar);
    overlay?.addEventListener('click', toggleSidebar);

    // Notifications
    document.getElementById('notificationBtn')?.addEventListener('click', () => {
        Swal.fire({
            title: 'Notifications',
            html: '• New order received<br>• Low stock alert<br>• Payment confirmed',
            icon: 'info',
            confirmButtonText: 'Okay'
        });
    });

    // Active link highlight
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath || currentPath.includes(link.getAttribute('href'))) {
            link.classList.add('bg-white/20', 'font-semibold');
        }
    });
});