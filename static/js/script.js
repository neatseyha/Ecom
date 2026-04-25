// Add to cart functionality
document.addEventListener("DOMContentLoaded", function () {
  console.log('%c🚀 DOMContentLoaded Event Fired', 'color: #10b981; font-weight: bold; font-size: 14px;');
  console.log('⏰ Page loaded at:', new Date().toLocaleTimeString());
  
  // Handle image loading errors with local placeholder
  const images = document.querySelectorAll('img');
  console.log(`📷 Found ${images.length} images`);
  
  images.forEach((img) => {
    img.addEventListener('error', function() {
      // Use local placeholder image served from Flask
      this.src = '/static/images/placeholder.png';
      this.style.backgroundColor = '#f0f0f0';
      this.style.objectFit = 'contain';
      this.style.padding = '20px';
    });
  });

  // Handle background images that fail to load
  const elementsWithBG = document.querySelectorAll('[style*="background-image"]');
  console.log(`🖼️  Found ${elementsWithBG.length} elements with background images`);
  
  elementsWithBG.forEach((el) => {
    const computedStyle = window.getComputedStyle(el);
    const bgImage = computedStyle.backgroundImage;
    if (bgImage && bgImage !== 'none') {
      const img = new Image();
      img.onerror = function() {
        el.style.backgroundColor = '#f0f0f0';
        el.style.backgroundImage = 'url(/static/images/placeholder.png)';
        el.style.backgroundSize = 'contain';
        el.style.backgroundPosition = 'center';
        el.style.backgroundRepeat = 'no-repeat';
      };
      const urlMatch = bgImage.match(/url\(["']?(.+?)["']?\)/);
      if (urlMatch) {
        img.src = urlMatch[1];
      }
    }
  });

  // Add to cart buttons
  const addToCartButtons = document.querySelectorAll(".add-to-cart");
  console.log(`%c🛒 Add to Cart Buttons Found: ${addToCartButtons.length}`, 'color: #2563eb; font-weight: bold; font-size: 14px;');
  
  if (addToCartButtons.length === 0) {
    console.error('%c❌ NO ADD TO CART BUTTONS FOUND!', 'color: #dc2626; font-weight: bold;');
    console.log('Available classes on page:', document.body.className);
  }
  
  addToCartButtons.forEach((button, index) => {
    console.log(`  Button ${index + 1}:`, {
      id: button.id,
      productId: button.dataset.productId,
      text: button.textContent.trim(),
      class: button.className
    });
    
    button.addEventListener("click", function () {
      const productId = parseInt(this.dataset.productId);
      console.log(`%c🔗 Click handler triggered for button ${index + 1}`, 'color: #2563eb; font-weight: bold;');
      addToCart(productId);
    });
  });
  
  console.log('✅ All click handlers attached successfully');

  // Quantity controls
  const increaseButtons = document.querySelectorAll(".qty-btn.increase");
  const decreaseButtons = document.querySelectorAll(".qty-btn.decrease");
  console.log(`📊 Quantity controls - Increase: ${increaseButtons.length}, Decrease: ${decreaseButtons.length}`);

  increaseButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const productId = parseInt(this.dataset.productId);
      const input = document.querySelector(
        `.quantity-input[data-product-id="${productId}"]`
      );
      const newQuantity = parseInt(input.value) + 1;
      updateCartQuantity(productId, newQuantity);
    });
  });

  decreaseButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const productId = parseInt(this.dataset.productId);
      const input = document.querySelector(
        `.quantity-input[data-product-id="${productId}"]`
      );
      const newQuantity = Math.max(1, parseInt(input.value) - 1);
      updateCartQuantity(productId, newQuantity);
    });
  });

  // Quantity input change
  const quantityInputs = document.querySelectorAll(".quantity-input");
  quantityInputs.forEach((input) => {
    input.addEventListener("change", function () {
      const productId = parseInt(this.dataset.productId);
      const newQuantity = Math.max(1, parseInt(this.value));
      this.value = newQuantity;
      updateCartQuantity(productId, newQuantity);
    });
  });

  // Remove from cart buttons
  const removeButtons = document.querySelectorAll(".remove-btn");
  removeButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const productId = parseInt(this.dataset.productId);
      removeFromCart(productId);
    });
  });
});

function addToCart(productId) {
  console.log('%c=== ADD TO CART CLICKED ===', 'color: #2563eb; font-weight: bold; font-size: 14px;');
  console.log('📦 Product ID:', productId);
  console.log('⏰ Timestamp:', new Date().toLocaleTimeString());
  
  // Find the button and disable it during request
  const button = document.querySelector(`.add-to-cart[data-product-id="${productId}"]`);
  console.log('🔘 Button found:', !!button);
  
  if (button) {
    const originalText = button.innerHTML;
    console.log('💾 Original button text saved');
    button.disabled = true;
    button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Adding...';
    console.log('⏳ Button disabled and showing "Adding..." spinner');
  }
  
  console.log('📡 Sending POST request to /add-to-cart');
  console.log('📤 Request body:', { product_id: productId });
  
  fetch("/add-to-cart", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ product_id: productId }),
  })
    .then((response) => {
      console.log('%c📥 Response Received', 'color: #059669; font-weight: bold;');
      console.log('✅ HTTP Status:', response.status);
      console.log('📋 Headers:', {
        'Content-Type': response.headers.get('Content-Type'),
        'Content-Length': response.headers.get('Content-Length')
      });
      
      // Handle 401 - user not logged in
      if (response.status === 401) {
        console.log('%c⚠️  UNAUTHORIZED - User not logged in', 'color: #dc2626; font-weight: bold;');
        if (button) {
          button.disabled = false;
          button.innerHTML = originalText;
          console.log('🔄 Button restored to original state');
        }
        showNotification("Please login to add items to cart", "info");
        console.log('⏭️  Redirecting to login page in 1.5 seconds...');
        setTimeout(() => {
          window.location.href = "/login";
        }, 1500);
        return null;
      }
      
      console.log('✨ Parsing JSON response...');
      return response.json();
    })
    .then((data) => {
      if (!data) {
        console.log('⚠️  No data returned (401 redirect)');
        return;
      }
      
      console.log('%c📊 Response Data', 'color: #7c3aed; font-weight: bold;');
      console.log(data);
      
      if (data.success) {
        console.log('%c✅ SUCCESS - Product added to cart!', 'color: #059669; font-weight: bold; font-size: 14px;');
        console.log('🛒 New cart count:', data.cart_count);
        
        // Update cart count badge
        const cartCount = document.getElementById("cart-count");
        if (cartCount) {
          cartCount.textContent = data.cart_count;
          cartCount.style.display = 'inline-block';
          console.log('📈 Cart badge updated to:', data.cart_count);
        } else {
          console.log('⚠️  Cart count badge element not found');
        }

        // Update button to show success
        if (button) {
          button.innerHTML = '<i class="fa-solid fa-check"></i> Added!';
          button.style.backgroundColor = '#28a745';
          console.log('✨ Button updated with success state (green checkmark)');
        }

        // Show success message with SweetAlert
        console.log('🎉 Showing SweetAlert notification...');
        Swal.fire({
          icon: 'success',
          title: 'Added to Cart!',
          text: 'Redirecting to cart page...',
          confirmButtonColor: '#28a745',
          timer: 1500,
          timerProgressBar: true,
          showConfirmButton: false
        }).then(() => {
          console.log('🛒 Redirecting to cart page...');
          window.location.href = '/cart';
        });
      } else {
        console.log('%c❌ FAILED - Server returned success: false', 'color: #dc2626; font-weight: bold;');
        console.log('💬 Error message:', data.message || "Unknown error");
        if (button) {
          button.disabled = false;
          button.innerHTML = originalText;
          console.log('🔄 Button restored to original state');
        }
        showNotification(data.message || "Failed to add product", "error");
      }
    })
    .catch((error) => {
      console.error('%c🔥 CATCH ERROR', 'color: #dc2626; font-weight: bold; font-size: 14px;');
      console.error('Error details:', error);
      console.error('Stack:', error.stack);
      if (button) {
        button.disabled = false;
        button.innerHTML = originalText;
        console.log('🔄 Button restored after error');
      }
      showNotification("Error adding to cart. Please try again.", "error");
    });
  
  console.log('%c=== REQUEST INITIATED ===', 'color: #2563eb; font-weight: bold;');
}

function updateCartQuantity(productId, quantity) {
  fetch("/update-cart", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      product_id: productId,
      quantity: quantity,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Reload page to update totals
        location.reload();
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("Failed to update cart", "error");
    });
}

function removeFromCart(productId) {
  if (confirm("Are you sure you want to remove this item?")) {
    fetch("/remove-from-cart", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ product_id: productId }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Reload page
          location.reload();
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        showNotification("Failed to remove item", "error");
      });
  }
}

function showNotification(message, type) {
  // Use the toast notification system from notifications.js
  if (typeof showToast === 'function') {
    showToast(message, type === 'success' ? 'success' : 'error');
  } else {
    // Fallback for when notifications.js is not loaded
    const notification = document.createElement("div");
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === "success" ? "#E2F167" : "#E64B4B"};
        color: white;
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.style.animation = "slideOut 0.3s ease-out";
      setTimeout(() => {
        notification.remove();
      }, 300);
    }, 3000);
  }
}

// Add animation styles
const style = document.createElement("style");
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Product interaction functions
function addToWishlist(productId, productName) {
  console.log('%c=== ADD TO WISHLIST CLICKED ===', 'color: #dc2626; font-weight: bold; font-size: 14px;');
  console.log('❤️  Product ID:', productId);
  console.log('📛 Product Name:', productName);
  console.log('⏰ Timestamp:', new Date().toLocaleTimeString());
  
  console.log('📡 Sending POST request to /add-to-wishlist');
  console.log('📤 Request body:', { product_id: productId, product_name: productName });
  
  fetch("/add-to-wishlist", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ 
      product_id: productId,
      product_name: productName
    }),
  })
    .then((response) => {
      console.log('%c📥 Response Received', 'color: #059669; font-weight: bold;');
      console.log('✅ HTTP Status:', response.status);
      
      // Handle 401 - user not logged in
      if (response.status === 401) {
        console.log('%c⚠️  UNAUTHORIZED - User not logged in', 'color: #dc2626; font-weight: bold;');
        showNotification("Please login to add items to wishlist", "info");
        console.log('⏭️  Redirecting to login page in 1.5 seconds...');
        setTimeout(() => {
          window.location.href = "/login";
        }, 1500);
        return null;
      }
      
      console.log('✨ Parsing JSON response...');
      return response.json();
    })
    .then((data) => {
      if (!data) {
        console.log('⚠️  No data returned (401 redirect)');
        return;
      }
      
      console.log('%c📊 Response Data', 'color: #7c3aed; font-weight: bold;');
      console.log(data);
      
      if (data.success) {
        const isAdded = data.action !== 'removed';
        const buttonSelectors = [`#wishlist-${productId}`, `#wishlist-detail-${productId}`];

        buttonSelectors.forEach((selector) => {
          const wishlistBtn = document.querySelector(selector);
          if (!wishlistBtn) {
            return;
          }

          wishlistBtn.classList.toggle('in-wishlist', isAdded);

          const icon = wishlistBtn.querySelector('i');
          if (icon) {
            icon.classList.toggle('fa-solid', isAdded);
            icon.classList.toggle('fa-regular', !isAdded);
            icon.classList.toggle('text-muted', !isAdded);
          }
        });

        Swal.fire({
          icon: 'success',
          title: isAdded ? 'Added to Wishlist!' : 'Removed from Wishlist',
          text: data.message || (isAdded ? 'Product added to your wishlist' : 'Product removed from your wishlist'),
          confirmButtonColor: '#dc3545',
          timer: 2000,
          timerProgressBar: true,
          showConfirmButton: false
        });
      } else {
        console.log('%c❌ FAILED - Server returned success: false', 'color: #dc2626; font-weight: bold;');
        console.log('💬 Error message:', data.message || "Unknown error");
        showNotification(data.message || "Failed to add to wishlist", "error");
      }
    })
    .catch((error) => {
      console.error('%c🔥 CATCH ERROR', 'color: #dc2626; font-weight: bold; font-size: 14px;');
      console.error('Error details:', error);
      console.error('Stack:', error.stack);
      showNotification("Error adding to wishlist. Please try again.", "error");
    });
  
  console.log('%c=== REQUEST INITIATED ===', 'color: #dc2626; font-weight: bold;');
}

function showQuickView(productId) {
  console.log('%c=== QUICK VIEW CLICKED ===', 'color: #f59e0b; font-weight: bold; font-size: 14px;');
  console.log('👁️  Product ID:', productId);
  console.log('⏰ Timestamp:', new Date().toLocaleTimeString());
  
  console.log('📡 Sending GET request to /api/product/' + productId);
  
  // Fetch product details
  fetch(`/api/product/${productId}`)
    .then((response) => {
      console.log('%c📥 Response Received', 'color: #059669; font-weight: bold;');
      console.log('✅ HTTP Status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      console.log('✨ Parsing JSON response...');
      return response.json();
    })
    .then((data) => {
      console.log('%c📊 Response Data', 'color: #7c3aed; font-weight: bold;');
      console.log(data);
      
      if (data.success) {
        console.log('%c✅ SUCCESS - Product data loaded!', 'color: #f59e0b; font-weight: bold; font-size: 14px;');
        console.log('📦 Product Details:', {
          id: data.product.id,
          name: data.product.name,
          price: data.product.price,
          description: data.product.description
        });
        
        // Create and show quick view modal
        console.log('🎨 Creating quick view modal...');
        const modal = createQuickViewModal(data.product);
        document.body.appendChild(modal);
        modal.classList.add('show');
        console.log('✨ Modal added to DOM and shown');
        
        // Handle close button
        const closeBtn = modal.querySelector('.btn-close');
        if (closeBtn) {
          closeBtn.addEventListener('click', () => {
            console.log('❌ Close button clicked, removing modal');
            modal.remove();
          });
        }
        
        // Close on background click
        modal.addEventListener('click', (e) => {
          if (e.target === modal) {
            console.log('❌ Modal background clicked, removing modal');
            modal.remove();
          }
        });
      } else {
        console.log('%c❌ FAILED - Server returned success: false', 'color: #f59e0b; font-weight: bold;');
        showNotification(data.message || "Failed to load product", "error");
      }
    })
    .catch((error) => {
      console.error('%c🔥 CATCH ERROR', 'color: #f59e0b; font-weight: bold; font-size: 14px;');
      console.error('Error details:', error);
      console.error('Stack:', error.stack);
      showNotification("Error loading product details. Please try again.", "error");
    });
  
  console.log('%c=== REQUEST INITIATED ===', 'color: #f59e0b; font-weight: bold;');
}

function createQuickViewModal(product) {
  const modal = document.createElement('div');
  modal.className = 'modal fade show';
  modal.style.display = 'block';
  modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
  modal.innerHTML = `
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Quick View</h5>
          <button type="button" class="btn-close"></button>
        </div>
        <div class="modal-body">
          <div class="row">
            <div class="col-md-6">
              <img src="${product.image || '/static/images/placeholder.png'}" class="img-fluid" alt="${product.name}">
            </div>
            <div class="col-md-6">
              <h3>${product.name}</h3>
              <p class="text-muted">${product.description || ''}</p>
              <div class="fs-5 fw-bold text-success mb-3">$${(product.price || 0).toFixed(2)}</div>
              <p><strong>Stock:</strong> <span class="badge bg-success">In Stock</span></p>
              <div class="mb-3">
                <button class="btn btn-success w-100" onclick="addToCart(${product.id})">
                  <i class="fas fa-shopping-cart me-2"></i>Add to Cart
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
  return modal;
}

// ✅ Scroll navbar shadow on scroll
(function() {
  const nav = document.querySelector('nav');
  if (!nav) return;
  
  const onScroll = () => {
    if (window.scrollY > 20) nav.classList.add('scrolled');
    else nav.classList.remove('scrolled');
  };
  document.addEventListener('scroll', onScroll, { passive: true });
  // run once
  onScroll();
})();

// ✅ Script.js fully loaded - Ready for interactions
console.log('%c✅ script.js fully loaded and ready!', 'color: #10b981; font-weight: bold; font-size: 14px;');
console.log('Available functions: addToCart(), addToWishlist(), showQuickView()');
