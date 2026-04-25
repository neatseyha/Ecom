// Toast Notification System
function showToast(message, type = 'success', duration = 3000) {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after duration
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

// Add to Cart with Toast
function addToCartWithNotification(productId, productName) {
    fetch('/add-to-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ product_id: productId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`✓ ${productName} added to cart!`, 'success', 2000);
            updateCartCount();
        } else {
            showToast(data.message || 'Error adding to cart', 'error');
        }
    })
    .catch(error => {
        showToast('Error adding to cart', 'error');
        console.error('Error:', error);
    });
}

// Add to Wishlist
function addToWishlist(productId, productName) {
    fetch('/add-to-wishlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ product_id: productId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`♥ ${productName} added to wishlist!`, 'success', 2000);
            document.querySelector(`[data-wishlist-btn="${productId}"]`)?.classList.add('in-wishlist');
        } else {
            showToast(data.message || 'Error adding to wishlist', 'error');
        }
    })
    .catch(error => {
        showToast('Please login to add to wishlist', 'error');
        console.error('Error:', error);
    });
}

// Remove from Wishlist
function removeFromWishlist(wishlistId, productName) {
    fetch('/remove-from-wishlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ wishlist_id: wishlistId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`Removed from wishlist`, 'success', 2000);
            location.reload();
        } else {
            showToast(data.message || 'Error removing from wishlist', 'error');
        }
    })
    .catch(error => {
        showToast('Error removing from wishlist', 'error');
    });
}

// Update Cart Count
function updateCartCount() {
    fetch('/cart')
    .then(response => response.text())
    .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const cartItems = doc.querySelectorAll('.cart-item-row').length;
        document.getElementById('cart-count').textContent = cartItems;
    })
    .catch(err => console.error('Error updating cart:', err));
}

// Form Validation
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 6;
}

function validateForm(formType) {
    if (formType === 'login') {
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        
        if (!email) {
            showToast('Please enter your email', 'error');
            return false;
        }
        if (!validateEmail(email)) {
            showToast('Please enter a valid email', 'error');
            return false;
        }
        if (!password) {
            showToast('Please enter your password', 'error');
            return false;
        }
        return true;
    }
    
    if (formType === 'signup') {
        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        
        if (!name) {
            showToast('Please enter your name', 'error');
            return false;
        }
        if (!email) {
            showToast('Please enter your email', 'error');
            return false;
        }
        if (!validateEmail(email)) {
            showToast('Please enter a valid email', 'error');
            return false;
        }
        if (!password) {
            showToast('Please enter a password', 'error');
            return false;
        }
        if (!validatePassword(password)) {
            showToast('Password must be at least 6 characters', 'error');
            return false;
        }
        if (password !== confirmPassword) {
            showToast('Passwords do not match', 'error');
            return false;
        }
        return true;
    }
    
    return true;
}

// Product Search
function searchProducts(query) {
    if (!query.trim()) {
        showToast('Please enter a search term', 'error');
        return;
    }
    window.location.href = `/shop?search=${encodeURIComponent(query)}`;
}

// Quick View Modal
function showQuickView(productId) {
    fetch(`/product/${productId}`)
    .then(response => response.text())
    .then(html => {
        const modal = document.getElementById('quickViewModal');
        const content = modal.querySelector('.modal-body');
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const productContent = doc.querySelector('.product-detail-layout');
        content.innerHTML = productContent ? productContent.innerHTML : 'Product not found';
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    })
    .catch(err => {
        showToast('Error loading product', 'error');
        console.error('Error:', err);
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add search functionality
    const searchBtn = document.getElementById('search-btn');
    const searchInput = document.getElementById('search-input');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            searchProducts(searchInput.value);
        });
    }
    
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchProducts(searchInput.value);
            }
        });
    }
    
    // Form validation
    const loginForm = document.querySelector('form[action*="/login"]');
    const signupForm = document.querySelector('form[action*="/signup"]');
    
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            if (!validateForm('login')) {
                e.preventDefault();
            }
        });
    }
    
    if (signupForm) {
        signupForm.addEventListener('submit', (e) => {
            if (!validateForm('signup')) {
                e.preventDefault();
            }
        });
    }
});
