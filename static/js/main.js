// ═══════════════════════════════════════════════════════════════
// 🏀 Basketball Shop — Main JavaScript
// ═══════════════════════════════════════════════════════════════

// ─── Cart Management ───
function getCart() {
    return JSON.parse(localStorage.getItem('cart') || '[]');
}

function saveCart(cart) {
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartCount();
}

function updateCartCount() {
    const cart = getCart();
    const total = cart.reduce((sum, item) => sum + item.qty, 0);
    const countEl = document.getElementById('cartCount');
    if (countEl) {
        countEl.textContent = total;
        countEl.style.display = total > 0 ? 'flex' : 'none';
    }
}

function addToCart(id, name, price, image, qty = 1) {
    qty = parseInt(qty) || 1;
    const cart = getCart();
    const existing = cart.find(item => item.id === id);

    if (existing) {
        existing.qty += qty;
    } else {
        cart.push({ id, name, price, image, qty });
    }

    saveCart(cart);
    showToast(`🛒 "${name}" savatga qo'shildi!`);
}

function removeFromCart(id) {
    let cart = getCart();
    cart = cart.filter(item => item.id !== id);
    saveCart(cart);
    renderCart();
}

function updateCartItemQty(id, delta) {
    const cart = getCart();
    const item = cart.find(item => item.id === id);
    if (item) {
        item.qty += delta;
        if (item.qty <= 0) {
            removeFromCart(id);
            return;
        }
        saveCart(cart);
        renderCart();
    }
}

// ─── Render Cart Page ───
function renderCart() {
    const cart = getCart();
    const itemsContainer = document.getElementById('cartItems');
    const emptyEl = document.getElementById('cartEmpty');
    const summaryEl = document.getElementById('cartSummary');
    const totalEl = document.getElementById('cartTotal');

    if (!itemsContainer) return;

    if (cart.length === 0) {
        emptyEl.style.display = 'block';
        summaryEl.style.display = 'none';
        itemsContainer.innerHTML = '';
        return;
    }

    emptyEl.style.display = 'none';
    summaryEl.style.display = 'block';

    let total = 0;
    itemsContainer.innerHTML = cart.map(item => {
        const itemTotal = item.price * item.qty;
        total += itemTotal;
        return `
            <div class="cart-item">
                <img src="${item.image}" alt="${item.name}">
                <div class="cart-item-info">
                    <div class="cart-item-name">${item.name}</div>
                    <div class="cart-item-price">${Number(item.price).toLocaleString()} so'm</div>
                </div>
                <div class="cart-item-qty">
                    <button class="qty-btn" onclick="updateCartItemQty(${item.id}, -1)">−</button>
                    <span class="qty-input" style="display:inline-flex;align-items:center;justify-content:center;">${item.qty}</span>
                    <button class="qty-btn" onclick="updateCartItemQty(${item.id}, 1)">+</button>
                </div>
                <div style="font-weight:700;color:var(--accent);min-width:120px;text-align:right;">
                    ${itemTotal.toLocaleString()} so'm
                </div>
                <button class="cart-item-remove" onclick="removeFromCart(${item.id})">✕</button>
            </div>
        `;
    }).join('');

    totalEl.textContent = total.toLocaleString() + " so'm";
}

// ─── Toast Notification ───
function showToast(message) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
}

// ─── Mobile Menu ───
document.addEventListener('DOMContentLoaded', function() {
    updateCartCount();

    const menuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    if (menuBtn && mobileMenu) {
        menuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('show');
        });
    }
});
