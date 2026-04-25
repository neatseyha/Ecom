/**
 * Common Alert Handler
 * Shows success/error messages from URL parameters
 */
function showAlertFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const message = urlParams.get('message');
    const type = urlParams.get('type');
    
    if (message && typeof Swal !== 'undefined') {
        Swal.fire({
            title: type === 'success' ? 'Success!' : 'Error!',
            text: message,
            icon: type === 'success' ? 'success' : 'error',
            confirmButtonText: 'OK'
        });
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

/**
 * Image Preview Handler
 * Handles click, drag-drop, and file selection for image uploads
 */
function setupImagePreview(previewElementId, inputElementId) {
    const imagePreview = document.getElementById(previewElementId);
    const imageInput = document.getElementById(inputElementId);
    
    if (!imagePreview || !imageInput) return;

    // Click to upload
    imagePreview.addEventListener('click', function() {
        imageInput.click();
    });

    // Display preview when file is selected
    imageInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                imagePreview.innerHTML = '<img src="' + event.target.result + '" alt="Product Image">';
                imagePreview.classList.add('has-image');
            };
            reader.readAsDataURL(file);
        }
    });

    // Drag and drop functionality
    imagePreview.addEventListener('dragover', function(e) {
        e.preventDefault();
        imagePreview.style.borderColor = 'var(--primary-green)';
        imagePreview.style.backgroundColor = '#f0f8f5';
    });

    imagePreview.addEventListener('dragleave', function(e) {
        e.preventDefault();
        imagePreview.style.borderColor = 'var(--border-color)';
        imagePreview.style.backgroundColor = 'var(--bg-light)';
    });

    imagePreview.addEventListener('drop', function(e) {
        e.preventDefault();
        imagePreview.style.borderColor = 'var(--border-color)';
        imagePreview.style.backgroundColor = 'var(--bg-light)';
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            imageInput.files = files;
            const event = new Event('change', { bubbles: true });
            imageInput.dispatchEvent(event);
        }
    });
}

/**
 * Delete Confirmation
 * Shows SweetAlert confirmation before deleting
 */
function confirmDelete(event, productId) {
    event.preventDefault();
    
    if (typeof Swal === 'undefined') {
        if (confirm('Are you sure you want to delete this product?')) {
            window.location.href = '/products/delete/' + productId;
        }
        return;
    }
    
    Swal.fire({
        title: 'Delete Product?',
        text: 'Are you sure? This product will be permanently removed.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d32f2f',
        cancelButtonColor: '#9e9e9e',
        confirmButtonText: 'Yes, Delete',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = '/products/delete/' + productId;
        }
    });
}

// Initialize on page load
window.addEventListener('load', function() {
    showAlertFromUrl();

    // Sidebar toggle: uses body class to control collapsed state and persists in localStorage
    const sidebarToggle = document.getElementById('sidebarToggle');
    function setSidebarCollapsed(collapsed) {
        if (collapsed) {
            document.documentElement.classList.add('sidebar-collapsed');
        } else {
            document.documentElement.classList.remove('sidebar-collapsed');
        }
        localStorage.setItem('sidebarCollapsed', collapsed ? '1' : '0');
    }

    // initialize from storage
    const stored = localStorage.getItem('sidebarCollapsed');
    if (stored === '1') {
        setSidebarCollapsed(true);
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            if (window.innerWidth <= 992) {
                document.documentElement.classList.toggle('sidebar-open');
                return;
            }

            const collapsed = document.documentElement.classList.toggle('sidebar-collapsed');
            localStorage.setItem('sidebarCollapsed', collapsed ? '1' : '0');
        });
    }

    // Theme: Auto-detect dark mode preference (no manual toggle)
    function applyTheme(isDark) {
        if (isDark) document.documentElement.setAttribute('data-theme', 'dark');
        else document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('themeDark', isDark ? '1' : '0');
    }

    // Initialize theme from storage or system preference
    const savedDark = localStorage.getItem('themeDark');
    if (savedDark === '1') applyTheme(true);
    else if (savedDark === '0') applyTheme(false);
    else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) applyTheme(true);

    // Palette: Keep default Indigo (no manual switching)
    function applyPalette(name) {
        document.documentElement.setAttribute('data-palette', name);
        localStorage.setItem('palette', name);
    }

    // Initialize palette from storage (default: indigo)
    const savedPalette = localStorage.getItem('palette') || 'indigo';
    applyPalette(savedPalette);

    document.addEventListener('click', function(e) {
        if (window.innerWidth > 992) return;

        const sidebar = document.getElementById('sidebar');
        const clickedToggle = e.target.closest('#sidebarToggle');
        const clickedSidebar = e.target.closest('#sidebar');

        if (!clickedToggle && !clickedSidebar && sidebar && document.documentElement.classList.contains('sidebar-open')) {
            document.documentElement.classList.remove('sidebar-open');
        }
    });

});
