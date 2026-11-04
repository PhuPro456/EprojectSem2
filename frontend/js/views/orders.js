import { api } from '../api.js';
import { state } from '../store.js';
import { emptyView, errorView, esc, money, statusPill } from '../ui.js';

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export async function renderOrders(main) {
  main.innerHTML = `
    <div class="page">
      <header class="page-head">
        <div>
          <p class="eyebrow">${esc(state.user?.name || 'Your account')}</p>
          <h1>Your orders</h1>
        </div>
        <a class="btn ghost" href="#/catalog">Continue shopping</a>
      </header>
      <div id="ordersList"><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line"></div></div>
    </div>`;

  const list = main.querySelector('#ordersList');
  try {
    const orders = await api.myOrders();
    if (!orders.length) {
      list.innerHTML = emptyView(
        'No orders yet',
        'Your first order will appear here once you check out.',
        '<a class="btn" href="#/catalog">Browse books</a>',
      );
      return;
    }
    list.innerHTML = `<div class="order-list">${orders
      .map(
        (order) => `<article class="order-card">
          <header>
            <div>
              <p class="order-id">Order #${order.id}</p>
              <p class="order-date">${esc(formatDate(order.created_at))}</p>
            </div>
            ${statusPill(order.status)}
          </header>
          <ul class="order-items">
            ${order.items
              .map(
                (item) => `<li><span>${esc(item.title)}</span><span class="muted">× ${item.quantity}</span><span>${money(item.unit_price * item.quantity)}</span></li>`,
              )
              .join('')}
          </ul>
          <footer>
            <span class="muted">${order.items.reduce((sum, item) => sum + item.quantity, 0)} item(s)</span>
            <strong>${money(order.total)}</strong>
          </footer>
        </article>`,
      )
      .join('')}</div>`;
  } catch (error) {
    list.innerHTML = errorView(error.message);
    list.querySelector('[data-retry]')?.addEventListener('click', () => renderOrders(main));
  }
}
