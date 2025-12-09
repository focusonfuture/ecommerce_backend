document.addEventListener('DOMContentLoaded', () => {

    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const navLinks = document.querySelectorAll('.nav-link');

    function toggleSidebar() {
        if (window.innerWidth <= 768) {
            sidebar.classList.toggle('open');
            sidebarOverlay.classList.toggle('active');
            document.body.style.overflow = sidebar.classList.contains('open') ? 'hidden' : '';
        } else {
            sidebar.classList.toggle('collapsed');
        }
    }

    menuToggle.addEventListener('click', toggleSidebar);
    sidebarOverlay.addEventListener('click', toggleSidebar); // Close sidebar when overlay is clicked

    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('open');
            sidebarOverlay.classList.remove('active');
            document.body.style.overflow = ''; // Restore body scrolling
        } else {
            if (sidebar.classList.contains('collapsed') && !sidebar.classList.contains('open')) {
                sidebar.classList.remove('collapsed');
            }
        }
    });

    // Highlight active sidebar link based on current path
    const currentPath = window.location.pathname;
    const breadcrumb = document.querySelector('.breadcrumb');

    navLinks.forEach(link => {
        const linkHref = link.getAttribute('href');

        if (currentPath === linkHref || currentPath.startsWith(linkHref)) {
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            const linkTextSpan = link.querySelector('span:not(.nav-icon)');
            const linkText = linkTextSpan ? linkTextSpan.textContent.trim() : link.getAttribute('data-tooltip');

            if (breadcrumb) {
                breadcrumb.innerHTML = `<span>Dashboard</span><span>•</span><span>${linkText}</span>`;
            }
        }
    });

    // Search bar simulation
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            if (searchTerm.length > 2) {
                console.log('Searching for:', searchTerm);
            }
        });
    }

    // Notifications
    const notificationBtn = document.querySelector('.notification-btn');
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function() {
            Swal.fire({
                title: 'Notifications',
                html: '• New order received<br>• Low stock alert<br>• Payment confirmation',
                icon: 'info',
                confirmButtonText: 'Got it!'
            });
        });
    }

    // User dropdown
    const userProfile = document.querySelector('.user-profile');
    if (userProfile) {
        userProfile.addEventListener('click', function() {
            const dropdown = document.createElement('div');
            dropdown.style.cssText = `
                position: absolute;
                top: 100%;
                right: 0;
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                padding: 8px 0;
                min-width: 150px;
                z-index: 1000;
            `;

            dropdown.innerHTML = `
                <a href="#" style="display: block; padding: 8px 16px; text-decoration: none; color: #1e293b; font-size: 14px;">My Profile</a>
                <a href="#" style="display: block; padding: 8px 16px; text-decoration: none; color: #1e293b; font-size: 14px;">Settings</a>
                <hr style="margin: 4px 0; border: none; border-top: 1px solid #f1f5f9;">
                <a href="#" style="display: block; padding: 8px 16px; text-decoration: none; color: #ef4444; font-size: 14px;">Logout</a>
            `;

            // Remove existing dropdown
            const existingDropdown = document.querySelector('.user-dropdown');
            if (existingDropdown) {
                existingDropdown.remove();
            }

            dropdown.className = 'user-dropdown';
            this.style.position = 'relative';
            this.appendChild(dropdown);

            // Remove dropdown when clicking outside
            setTimeout(() => {
                document.addEventListener('click', function removeDropdown(e) {
                    if (!userProfile.contains(e.target)) {
                        dropdown.remove();
                        document.removeEventListener('click', removeDropdown);
                    }
                });
            }, 100);
        });
    }

    // Stat animation
    function updateStats() {
        const statValues = document.querySelectorAll('.stat-value');
        statValues.forEach((stat, index) => {
            stat.style.transform = 'scale(1.05)';
            stat.style.transition = 'transform 0.2s ease';
            setTimeout(() => {
                stat.style.transform = 'scale(1)';
            }, 200);
        });
    }

    // Update stats every 30 seconds
    setInterval(updateStats, 30000);

    // Loading effect (used for charts, etc.)
    function showLoading(element) {
        element.style.opacity = '0.5';
        element.style.pointerEvents = 'none';
        const loadingDiv = document.createElement('div');
        loadingDiv.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 16px; color: #64748b;';
        loadingDiv.textContent = 'Loading...';
        element.appendChild(loadingDiv);
    }

    function hideLoading(element) {
        element.style.opacity = '1';
        element.style.pointerEvents = 'auto';
        const loadingText = element.querySelector('div[style*="position: absolute"]');
        if (loadingText) {
            loadingText.remove();
        }
    }

    const chartPlaceholders = document.querySelectorAll('.chart-placeholder');
    chartPlaceholders.forEach(chart => {
        showLoading(chart);
        setTimeout(() => hideLoading(chart), 2000);
    });

});
