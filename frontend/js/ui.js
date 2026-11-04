export const ICONS = {
  search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
  cart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/><path d="M3 4h2l2.4 12.1a2 2 0 0 0 2 1.9h7.7a2 2 0 0 0 2-1.6L21 8H6"/></svg>',
  user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.6-6 8-6s8 2 8 6"/></svg>',
  receipt: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6"/></svg>',
  close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 6l12 12M18 6 6 18"/></svg>',
  arrowLeft: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M15 5l-7 7 7 7"/></svg>',
  spark: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/></svg>',
  box: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M21 8l-9-5-9 5v8l9 5 9-5z"/><path d="M3 8l9 5 9-5M12 13v8"/></svg>',
  users: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="9" cy="8" r="4"/><path d="M2 21c0-4 3-6 7-6s7 2 7 6"/><circle cx="17" cy="9" r="3"/><path d="M17 15c3 0 5 2 5 5"/></svg>',
  chart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 20V4M4 20h16"/><path d="M8 17v-5M12.5 17V8M17 17v-7"/></svg>',
  book: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 5a2 2 0 0 1 2-2h5v18H6a2 2 0 0 1-2-2z"/><path d="M20 5a2 2 0 0 0-2-2h-5v18h5a2 2 0 0 0 2-2z"/></svg>',
  logout: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M9 4H5v16h4"/><path d="M14 8l4 4-4 4M18 12H9"/></svg>',
  trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14"/></svg>',
  edit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16z"/></svg>',
  plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 5v14M5 12h14"/></svg>',
  minus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 12h14"/></svg>',
};

const ENTITIES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

export function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ENTITIES[char]);
}

export function money(value) {
  return '$' + Number(value || 0).toFixed(2);
}

export function categoryName(code) {
  return String(code || '')
    .split('-')
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function stockLabel(stock) {
  if (stock <= 0) return '<span class="stock out">Out of stock</span>';
  if (stock <= 10) return `<span class="stock low">Only ${stock} left</span>`;
  return '<span class="stock">In stock</span>';
}

export function bookCard(book) {
  return `<article class="book-card">
    <a class="book-cover" href="#/book/${book.id}" aria-label="${esc(book.title)}">
      <img src="${esc(book.cover)}" alt="Cover of ${esc(book.title)}" loading="lazy">
    </a>
    <a class="book-cat" href="#/catalog?category=${encodeURIComponent(book.category)}">${esc(categoryName(book.category))}</a>
    <h3 class="book-title"><a href="#/book/${book.id}">${esc(book.title)}</a></h3>
    <p class="book-author">${esc(book.author)}</p>
    <div class="book-meta"><span class="price">${money(book.price)}</span>${stockLabel(book.stock)}</div>
  </article>`;
}

export function statusPill(status) {
  return `<span class="pill status-${esc(status)}">${esc(status)}</span>`;
}

export function debounce(fn, wait = 260) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
}

export function toast(message, kind = 'info') {
  const root = document.getElementById('toastRoot');
  if (!root) return;
  const node = document.createElement('div');
  node.className = `toast toast-${kind}`;
  node.textContent = message;
  root.appendChild(node);
  setTimeout(() => {
    node.classList.add('leaving');
    setTimeout(() => node.remove(), 260);
  }, 3400);
}

export function skeletonGrid(count = 12) {
  return `<div class="book-grid">${Array.from({ length: count }, () => `
    <div class="book-card skeleton-card">
      <div class="skeleton skeleton-cover"></div>
      <div class="skeleton skeleton-line short"></div>
      <div class="skeleton skeleton-line"></div>
      <div class="skeleton skeleton-line tiny"></div>
    </div>`).join('')}</div>`;
}

export function errorView(message, { retry = true } = {}) {
  return `<div class="state-card">
    <h3>Something went wrong</h3>
    <p>${esc(message)}</p>
    ${retry ? '<button class="btn" data-retry>Try again</button>' : ''}
  </div>`;
}

export function emptyView(title, message, action = '') {
  return `<div class="state-card">
    <h3>${esc(title)}</h3>
    <p>${esc(message)}</p>
    ${action}
  </div>`;
}

export function openModal({ title, body, footer = '', onMount }) {
  const root = document.getElementById('modalRoot');
  if (!root) return () => {};
  root.innerHTML = `<div class="modal-backdrop" data-modal-close>
    <section class="modal" role="dialog" aria-modal="true">
      <header class="modal-head">
        <h2>${esc(title)}</h2>
        <button class="icon-btn" type="button" data-modal-close aria-label="Close">${ICONS.close}</button>
      </header>
      <div class="modal-body">${body}</div>
      ${footer ? `<footer class="modal-foot">${footer}</footer>` : ''}
    </section>
  </div>`;
  const close = () => {
    root.innerHTML = '';
    document.body.classList.remove('modal-open');
  };
  document.body.classList.add('modal-open');
  root.querySelectorAll('[data-modal-close]').forEach((node) => {
    node.addEventListener('click', (event) => {
      if (event.target === node) close();
    });
  });
  document.addEventListener('keydown', function onKey(event) {
    if (event.key === 'Escape') {
      close();
      document.removeEventListener('keydown', onKey);
    }
  });
  if (onMount) onMount(root.querySelector('.modal'), close);
  return close;
}

export function applyRetry(container, retry) {
  const button = container.querySelector('[data-retry]');
  if (button) button.addEventListener('click', retry);
}
