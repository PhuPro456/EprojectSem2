import { api } from './api.js';
import {
  cartClear,
  cartCount,
  cartRemove,
  cartSetQuantity,
  cartTotal,
  isAdmin,
  loadUser,
  logout,
  state,
  subscribe,
} from './store.js';
import { ICONS, esc, money, toast } from './ui.js';
import {
  renderAdminBooks,
  renderAdminCustomers,
  renderAdminOrders,
  renderAdminOverview,
} from './views/admin.js';
import { renderAdminAnalytics, renderAdminReviews } from './views/analytics.js';
import { renderAi } from './views/ai.js';
import { renderLogin, renderRegister } from './views/auth.js';
import { renderBook } from './views/book.js';
import { renderCatalog } from './views/catalog.js';
import { renderHome } from './views/home.js';
import { renderOrders } from './views/orders.js';

const menuIcon =
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16M4 12h16M4 17h16"/></svg>';

const ROUTES = [
  { pattern: /^\/?$/, layout: 'store', title: 'Home', render: (main) => renderHome(main) },
  {
    pattern: /^\/catalog$/,
    layout: 'store',
    title: 'Books',
    render: (main) => renderCatalog(main),
  },
  {
    pattern: /^\/book\/(\d+)$/,
    layout: 'store',
    title: 'Book',
    render: (main, match) => renderBook(main, match[1]),
  },
  {
    pattern: /^\/ai$/,
    layout: 'store',
    title: 'AI assistant',
    render: (main) => renderAi(main),
  },
  {
    pattern: /^\/login$/,
    layout: 'auth',
    title: 'Sign in',
    render: (main) => renderLogin(main),
  },
  {
    pattern: /^\/register$/,
    layout: 'auth',
    title: 'Create account',
    render: (main) => renderRegister(main),
  },
  {
    pattern: /^\/orders$/,
    layout: 'store',
    title: 'Your orders',
    requiresAuth: true,
    render: (main) => renderOrders(main),
  },
  {
    pattern: /^\/admin$/,
    layout: 'admin',
    title: 'Overview',
    adminTitle: 'Overview',
    requiresAdmin: true,
    render: (main) => renderAdminOverview(main),
  },
  {
    pattern: /^\/admin\/books$/,
    layout: 'admin',
    title: 'Books',
    adminTitle: 'Books',
    requiresAdmin: true,
    render: (main) => renderAdminBooks(main),
  },
  {
    pattern: /^\/admin\/orders$/,
    layout: 'admin',
    title: 'Orders',
    adminTitle: 'Orders',
    requiresAdmin: true,
    render: (main) => renderAdminOrders(main),
  },
  {
    pattern: /^\/admin\/customers$/,
    layout: 'admin',
    title: 'Customers',
    adminTitle: 'Customers',
    requiresAdmin: true,
    render: (main) => renderAdminCustomers(main),
  },
  {
    pattern: /^\/admin\/analytics$/,
    layout: 'admin',
    title: 'Analytics',
    adminTitle: 'Analytics',
    requiresAdmin: true,
    render: (main) => renderAdminAnalytics(main),
  },
  {
    pattern: /^\/admin\/reviews$/,
    layout: 'admin',
    title: 'Reviews',
    adminTitle: 'Reviews',
    requiresAdmin: true,
    render: (main) => renderAdminReviews(main),
  },
];

let shellLayout = null;
let booted = false;
let routeToken = 0;
let pendingCartOpen = false;

function parseHash() {
  const raw = (location.hash || '').replace(/^#/, '');
  const [rawPath, rawQuery = ''] = raw.split('?');
  let pathname = rawPath || '/';
  if (!pathname.startsWith('/')) pathname = `/${pathname}`;
  if (pathname.length > 1) pathname = pathname.replace(/\/+$/, '');
  return { pathname, search: rawQuery ? `?${rawQuery}` : '' };
}

function initials(name) {
  return String(name || '?')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('');
}

function userName() {
  return state.user?.name?.split(/\s+/)[0] || 'Sign in';
}

function accountMenu() {
  if (!state.user) {
    return `<div class="account-menu" data-account-menu hidden>
      <div class="account-head"><strong>Welcome</strong><span>Sign in to check out faster and keep track of your orders.</span></div>
      <a href="#/login">${ICONS.user}<span>Sign in</span></a>
      <a href="#/register">${ICONS.plus}<span>Create account</span></a>
    </div>`;
  }
  return `<div class="account-menu" data-account-menu hidden>
    <div class="account-head"><strong>${esc(state.user.name)}</strong><span>${esc(state.user.email)}</span></div>
    <a href="#/orders">${ICONS.receipt}<span>Your orders</span></a>
    <a href="#/ai">${ICONS.spark}<span>AI reading room</span></a>
    ${isAdmin() ? `<a href="#/admin">${ICONS.chart}<span>Admin console</span></a>` : ''}
    <button type="button" data-logout>${ICONS.logout}<span>Sign out</span></button>
  </div>`;
}

function cartLayer() {
  return `<div class="cart-layer" id="cartLayer" hidden>
    <div class="cart-backdrop" data-cart-close></div>
    <aside class="cart-drawer" role="dialog" aria-modal="true" aria-label="Shopping cart">
      <header class="cart-head">
        <div><p class="eyebrow">Your bag</p><h2>Cart</h2></div>
        <button class="icon-btn" type="button" data-cart-close aria-label="Close cart">${ICONS.close}</button>
      </header>
      <div class="cart-body" id="cartBody"></div>
      <footer class="cart-foot" id="cartFoot"></footer>
    </aside>
  </div>`;
}

function storeShell() {
  return `<div class="store-shell">
    <div class="announce"><span>Free shipping on orders over $35</span><span class="announce-dot" aria-hidden="true">·</span><span>30-day returns</span></div>
    <header class="site-header">
      <div class="header-inner">
        <a class="wordmark" href="#/">Bookstore<span>Pro</span></a>
        <nav class="main-nav" aria-label="Primary">
          <a href="#/" data-nav="home">Home</a>
          <a href="#/catalog" data-nav="catalog">All books</a>
          <a href="#/catalog?category=science-fiction" data-nav="scifi">Sci-fi</a>
          <a href="#/catalog?category=mystery" data-nav="mystery">Mystery</a>
          <a href="#/ai" data-nav="ai">AI assistant</a>
          <a href="#/orders" data-nav="orders">Orders</a>
          ${isAdmin() ? '<a href="#/admin" data-nav="admin">Admin</a>' : ''}
        </nav>
        <div class="header-actions">
          <form class="header-search" data-header-search role="search">
            ${ICONS.search}
            <input name="q" type="search" placeholder="Search books" aria-label="Search books" autocomplete="off">
          </form>
          <a class="icon-btn orders-link" href="#/orders" aria-label="Your orders">${ICONS.receipt}</a>
          <div class="account" data-account>
            <button class="account-btn" type="button" data-account-toggle aria-haspopup="true" aria-expanded="false">
              ${ICONS.user}<span class="account-name">${esc(userName())}</span>
            </button>
            ${accountMenu()}
          </div>
          <button class="cart-btn" type="button" data-open-cart aria-label="Open cart">
            ${ICONS.cart}<span class="badge" data-cart-badge hidden>0</span>
          </button>
          <button class="icon-btn nav-toggle" type="button" data-nav-toggle aria-label="Toggle navigation" aria-expanded="false">${menuIcon}</button>
        </div>
      </div>
    </header>
    <main id="main" class="site-main"></main>
    <footer class="site-footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <a class="wordmark light" href="#/">Bookstore<span>Pro</span></a>
          <p>A hundred real titles, five shelves, and a demo checkout built on FastAPI, PostgreSQL and vanilla JavaScript.</p>
        </div>
        <div class="footer-col">
          <h4>Shop</h4>
          <a href="#/catalog">All books</a>
          <a href="#/catalog?category=fantasy">Fantasy</a>
          <a href="#/catalog?category=mystery">Mystery</a>
          <a href="#/catalog?category=science-fiction">Science fiction</a>
        </div>
        <div class="footer-col">
          <h4>Account</h4>
          <a href="#/orders">Your orders</a>
          <a href="#/login">Sign in</a>
          <a href="#/register">Create account</a>
        </div>
        <div class="footer-col">
          <h4>Under the hood</h4>
          <span>FastAPI · SQLAlchemy</span>
          <span>PostgreSQL · JWT auth</span>
          <span>Vanilla JS · SVG covers</span>
        </div>
      </div>
      <p class="footer-fine">© 2026 Bookstore Pro — an FPT e-project demo. Prices, inventory and orders are fictional.</p>
    </footer>
    ${cartLayer()}
  </div>`;
}

function adminShell() {
  return `<div class="admin-shell">
    <aside class="admin-sidebar">
      <div class="sidebar-brand">
        <a class="wordmark light" href="#/">Bookstore<span>Pro</span></a>
        <span class="admin-chip">Admin</span>
      </div>
      <nav class="admin-nav" aria-label="Administration">
        <a href="#/admin" data-admin-nav="overview">${ICONS.chart}<span>Overview</span></a>
        <a href="#/admin/books" data-admin-nav="books">${ICONS.book}<span>Books</span></a>
        <a href="#/admin/orders" data-admin-nav="orders">${ICONS.receipt}<span>Orders</span></a>
        <a href="#/admin/customers" data-admin-nav="customers">${ICONS.users}<span>Customers</span></a>
        <a href="#/admin/analytics" data-admin-nav="analytics">${ICONS.chart}<span>Analytics</span></a>
        <a href="#/admin/reviews" data-admin-nav="reviews">${ICONS.spark}<span>Reviews</span></a>
      </nav>
      <div class="sidebar-foot">
        <a class="sidebar-link" href="#/">${ICONS.arrowLeft}<span>Storefront</span></a>
        <button class="sidebar-link" type="button" data-logout>${ICONS.logout}<span>Sign out</span></button>
      </div>
    </aside>
    <div class="admin-frame">
      <header class="admin-topbar">
        <button class="icon-btn admin-nav-toggle" type="button" data-admin-nav-toggle aria-label="Toggle sidebar">${menuIcon}</button>
        <div class="admin-title"><p class="eyebrow">Administration</p><h1 data-admin-title>Overview</h1></div>
        <div class="admin-user">
          <span class="avatar">${esc(initials(state.user?.name))}</span>
          <div><strong>${esc(state.user?.name || 'Admin')}</strong><span class="muted">${esc(state.user?.email || '')}</span></div>
        </div>
      </header>
      <main id="main" class="admin-main"></main>
    </div>
  </div>`;
}

function authShell() {
  return `<div class="auth-shell">
    <header class="auth-top">
      <a class="wordmark" href="#/">Bookstore<span>Pro</span></a>
      <a class="link-arrow" href="#/">Back to the store <span aria-hidden="true">→</span></a>
    </header>
    <main id="main" class="auth-main"></main>
  </div>`;
}

function shellFor(layout) {
  if (layout === 'admin') return adminShell();
  if (layout === 'auth') return authShell();
  return storeShell();
}

function ensureShell(layout) {
  const app = document.getElementById('app');
  if (shellLayout === layout && app.firstElementChild) return;
  app.innerHTML = shellFor(layout);
  shellLayout = layout;
  document.body.classList.toggle('admin-body', layout === 'admin');
  updateCartBadge();
}

function mountMain() {
  const previous = document.getElementById('main');
  const main = document.createElement('main');
  main.id = 'main';
  main.className = previous?.className || '';
  if (previous) previous.replaceWith(main);
  else document.getElementById('app').appendChild(main);
  return main;
}

function updateActiveNav(pathname, search) {
  const category = new URLSearchParams(search.slice(1)).get('category');
  let key = null;
  if (pathname === '/') key = 'home';
  else if (pathname === '/catalog') {
    key = category === 'science-fiction' ? 'scifi' : category === 'mystery' ? 'mystery' : 'catalog';
  } else if (pathname === '/orders') key = 'orders';
  else if (pathname === '/ai') key = 'ai';
  else if (pathname.startsWith('/admin')) key = 'admin';

  document.querySelectorAll('[data-nav]').forEach((link) => {
    link.classList.toggle('active', link.dataset.nav === key);
  });

  const adminKey =
    pathname === '/admin'
      ? 'overview'
      : pathname.startsWith('/admin/')
        ? pathname.split('/')[2]
        : null;
  document.querySelectorAll('[data-admin-nav]').forEach((link) => {
    link.classList.toggle('active', link.dataset.adminNav === adminKey);
  });
}

function updateCartBadge() {
  const count = cartCount();
  document.querySelectorAll('[data-cart-badge]').forEach((badge) => {
    badge.textContent = String(count);
    badge.hidden = count === 0;
  });
}

function closeAccountMenu() {
  const menu = document.querySelector('[data-account-menu]');
  if (!menu) return;
  menu.hidden = true;
  document.querySelector('[data-account-toggle]')?.setAttribute('aria-expanded', 'false');
}

function openCart() {
  const layer = document.getElementById('cartLayer');
  if (!layer) {
    pendingCartOpen = true;
    return;
  }
  pendingCartOpen = false;
  closeAccountMenu();
  layer.hidden = false;
  document.body.classList.add('cart-open');
  renderCart();
  layer.querySelector('.cart-head .icon-btn')?.focus();
}

function closeCart() {
  const layer = document.getElementById('cartLayer');
  if (!layer) return;
  layer.hidden = true;
  document.body.classList.remove('cart-open');
}

function renderCart() {
  updateCartBadge();
  const body = document.getElementById('cartBody');
  const foot = document.getElementById('cartFoot');
  if (!body || !foot) return;

  if (!state.cart.length) {
    body.innerHTML = `<div class="cart-empty">
      ${ICONS.cart}
      <h3>Your cart is empty</h3>
      <p>Add a few titles and they will show up here.</p>
      <a class="btn" href="#/catalog" data-cart-close>Browse books</a>
    </div>`;
    foot.innerHTML = '';
    return;
  }

  body.innerHTML = `<ul class="cart-items">${state.cart
    .map(
      (item) => `<li class="cart-item">
        <img class="cart-thumb" src="${esc(item.cover || '')}" alt="" loading="lazy">
        <div class="cart-item-main">
          <a class="cart-title" href="#/book/${item.book_id}">${esc(item.title)}</a>
          <span class="muted cart-author">${esc(item.author)}</span>
          <div class="cart-item-row">
            <div class="cart-qty" role="group" aria-label="Quantity for ${esc(item.title)}">
              <button type="button" data-dec="${item.book_id}" aria-label="Decrease quantity">${ICONS.minus}</button>
              <span>${item.quantity}</span>
              <button type="button" data-inc="${item.book_id}" aria-label="Increase quantity">${ICONS.plus}</button>
            </div>
            <strong>${money(item.price * item.quantity)}</strong>
          </div>
        </div>
        <button class="icon-btn danger" type="button" data-remove="${item.book_id}" aria-label="Remove ${esc(item.title)}">${ICONS.trash}</button>
      </li>`,
    )
    .join('')}</ul>`;

  const total = cartTotal();
  foot.innerHTML = `<div class="cart-subtotal"><span>Subtotal</span><strong>${money(total)}</strong></div>
    <p class="cart-note">${total >= 35 ? 'Free shipping is included in this order.' : `Add ${money(35 - total)} more for free shipping.`}</p>
    <button class="btn full" type="button" id="checkoutBtn">${state.user ? 'Checkout' : 'Sign in & checkout'}</button>
    <p class="cart-fine">Demo store — no payment is taken.</p>`;

  foot.querySelector('#checkoutBtn')?.addEventListener('click', checkout);
}

async function checkout() {
  if (!state.cart.length) return;
  if (!state.user) {
    sessionStorage.setItem('bookstore.next', '#/orders');
    sessionStorage.setItem('bookstore.reopenCart', '1');
    closeCart();
    location.hash = '#/login';
    toast('Sign in to place your order', 'info');
    return;
  }
  const button = document.getElementById('checkoutBtn');
  if (button) {
    button.disabled = true;
    button.textContent = 'Placing order…';
  }
  try {
    const order = await api.checkout(
      state.cart.map(({ book_id, quantity }) => ({ book_id, quantity })),
    );
    cartClear();
    closeCart();
    toast(`Order #${order.id} placed`, 'success');
    if (location.hash === '#/orders') renderRoute();
    else location.hash = '#/orders';
  } catch (error) {
    toast(error.message, 'error');
    if (button) {
      button.disabled = false;
      button.textContent = state.user ? 'Checkout' : 'Sign in & checkout';
    }
  }
}

async function renderRoute() {
  if (!booted) return;
  const token = ++routeToken;
  const { pathname, search } = parseHash();
  const route = ROUTES.find((candidate) => candidate.pattern.test(pathname));
  const match = route ? pathname.match(route.pattern) : null;

  if (route?.requiresAuth && !state.user) {
    sessionStorage.setItem('bookstore.next', location.hash || '#/');
    location.hash = '#/login';
    return;
  }
  if (route?.requiresAdmin && !isAdmin()) {
    if (!state.user) {
      sessionStorage.setItem('bookstore.next', location.hash || '#/');
      location.hash = '#/login';
    } else {
      toast('Administrator access is required', 'error');
      location.hash = '#/';
    }
    return;
  }

  closeCart();
  closeAccountMenu();
  document.querySelector('.store-shell')?.classList.remove('nav-open');
  document.querySelector('.admin-shell')?.classList.remove('admin-nav-open');

  const layout = route?.layout || 'store';
  ensureShell(layout);
  const main = mountMain();
  updateActiveNav(pathname, search);
  document.title = route ? `${route.title} · Bookstore Pro` : 'Page not found · Bookstore Pro';
  const adminTitle = document.querySelector('[data-admin-title]');
  if (adminTitle) adminTitle.textContent = route?.adminTitle || 'Overview';
  window.scrollTo(0, 0);

  if (!route) {
    main.innerHTML = `<div class="page"><div class="state-card">
      <p class="eyebrow">404</p>
      <h3>Page not found</h3>
      <p>The page you were looking for does not exist or has moved.</p>
      <a class="btn" href="#/">Back to the store</a>
    </div></div>`;
    return;
  }

  try {
    await route.render(main, match);
  } catch (error) {
    if (token !== routeToken) return;
    main.innerHTML = `<div class="page"><div class="state-card">
      <h3>Something went wrong</h3>
      <p>${esc(error.message)}</p>
      <button class="btn" type="button" id="routeRetry">Try again</button>
    </div></div>`;
    main.querySelector('#routeRetry')?.addEventListener('click', renderRoute);
    toast(error.message, 'error');
  }
  if (pendingCartOpen) openCart();
}

document.addEventListener('click', (event) => {
  const inc = event.target.closest('[data-inc]');
  if (inc) {
    const item = state.cart.find((entry) => entry.book_id === Number(inc.dataset.inc));
    if (item) cartSetQuantity(item.book_id, item.quantity + 1);
    return;
  }
  const dec = event.target.closest('[data-dec]');
  if (dec) {
    const item = state.cart.find((entry) => entry.book_id === Number(dec.dataset.dec));
    if (item) cartSetQuantity(item.book_id, item.quantity - 1);
    return;
  }
  const remove = event.target.closest('[data-remove]');
  if (remove) {
    cartRemove(Number(remove.dataset.remove));
    return;
  }

  if (event.target.closest('[data-open-cart]')) {
    event.preventDefault();
    openCart();
    return;
  }
  if (event.target.closest('[data-cart-close]')) {
    closeCart();
  }
  if (event.target.closest('#cartBody a')) {
    closeCart();
  }

  const accountToggle = event.target.closest('[data-account-toggle]');
  if (accountToggle) {
    const menu = document.querySelector('[data-account-menu]');
    if (menu) {
      menu.hidden = !menu.hidden;
      accountToggle.setAttribute('aria-expanded', String(!menu.hidden));
    }
    return;
  }
  if (!event.target.closest('[data-account]')) closeAccountMenu();

  if (event.target.closest('[data-logout]')) {
    closeAccountMenu();
    if (location.hash.startsWith('#/admin')) location.hash = '#/';
    logout();
    toast('Signed out', 'info');
    return;
  }

  if (event.target.closest('[data-nav-toggle]')) {
    document.querySelector('.store-shell')?.classList.toggle('nav-open');
    return;
  }
  if (event.target.closest('[data-admin-nav-toggle]')) {
    document.querySelector('.admin-shell')?.classList.toggle('admin-nav-open');
    return;
  }
  if (event.target.closest('.main-nav a')) {
    document.querySelector('.store-shell')?.classList.remove('nav-open');
  }
  if (event.target.closest('[data-admin-nav]')) {
    document.querySelector('.admin-shell')?.classList.remove('admin-nav-open');
  }
});

document.addEventListener('submit', (event) => {
  const form = event.target.closest('[data-header-search]');
  if (!form) return;
  event.preventDefault();
  const query = form.q.value.trim();
  const next = query ? `#/catalog?q=${encodeURIComponent(query)}` : '#/catalog';
  if (location.hash === next) renderRoute();
  else location.hash = next;
  form.reset();
});

document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  closeCart();
  closeAccountMenu();
  document.querySelector('.store-shell')?.classList.remove('nav-open');
  document.querySelector('.admin-shell')?.classList.remove('admin-nav-open');
});

document.addEventListener('open-cart', () => openCart());

document.addEventListener(
  'error',
  (event) => {
    const image = event.target;
    if (!(image instanceof HTMLImageElement) || image.dataset.failed) return;
    image.dataset.failed = 'true';
    image.classList.add('is-broken');
    image.closest('.book-cover, .detail-cover, .cat-covers')?.classList.add('cover-missing');
  },
  true,
);

subscribe((_, event) => {
  if (!booted) return;
  if (event === 'cart') {
    updateCartBadge();
    renderCart();
    return;
  }
  if (event === 'auth') {
    const { pathname } = parseHash();
    if (state.user && (pathname === '/login' || pathname === '/register')) return;
    renderRoute();
  }
});

async function boot() {
  await loadUser();
  booted = true;
  updateCartBadge();
  renderCart();
  await renderRoute();
  window.addEventListener('hashchange', renderRoute);
}

boot();
