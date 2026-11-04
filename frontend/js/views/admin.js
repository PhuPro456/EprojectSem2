import { api } from '../api.js';
import {
  ICONS,
  categoryName,
  debounce,
  emptyView,
  errorView,
  esc,
  money,
  openModal,
  statusPill,
  toast,
} from '../ui.js';

const STATUSES = ['pending', 'paid', 'shipped', 'completed', 'cancelled'];
const NEXT_STATUS = {
  pending: ['paid', 'cancelled'],
  paid: ['shipped', 'cancelled'],
  shipped: ['completed'],
  completed: [],
  cancelled: [],
};

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

async function fetchAllBooks() {
  const books = [];
  let skip = 0;
  for (;;) {
    const page = await api.listBooks({ limit: 50, skip, sort_by: 'id', order: 'asc' });
    books.push(...page.items);
    skip += 50;
    if (skip >= page.total) break;
  }
  return books;
}

function stockPill(stock) {
  if (stock <= 0) return '<span class="pill status-cancelled">Out of stock</span>';
  if (stock <= 10) return '<span class="pill status-pending">Low stock</span>';
  return '<span class="pill status-completed">In stock</span>';
}

function thumb(book) {
  return book.cover
    ? `<img class="thumb" src="${esc(book.cover)}" alt="" loading="lazy">`
    : '<span class="thumb thumb-empty">—</span>';
}

function kpi(icon, label, value, hint) {
  return `<article class="kpi">
    <span class="kpi-icon">${icon}</span>
    <div><span class="kpi-label">${esc(label)}</span><strong>${esc(value)}</strong><span class="kpi-hint">${esc(hint)}</span></div>
  </article>`;
}

export async function renderAdminOverview(main) {
  main.innerHTML = `
    <div class="admin-page">
      <div class="kpi-grid" id="adminKpis">
        ${['', '', '', '', ''].map(() => '<div class="kpi skeleton" style="height:104px"></div>').join('')}
      </div>
      <div class="admin-columns">
        <section class="panel">
          <header class="panel-head"><h2>Needs attention</h2><a class="link-arrow" href="#/admin/books">Manage books →</a></header>
          <div id="lowStock"><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line"></div></div>
        </section>
        <section class="panel">
          <header class="panel-head"><h2>Recent orders</h2><a class="link-arrow" href="#/admin/orders">All orders →</a></header>
          <div id="recentOrders"><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line"></div></div>
        </section>
      </div>
    </div>`;

  try {
    const [stats, books, orders] = await Promise.all([
      api.stats(),
      fetchAllBooks(),
      api.admin.orders({ limit: 5 }),
    ]);
    const low = books.filter((book) => book.stock <= 10).sort((a, b) => a.stock - b.stock);
    const out = books.filter((book) => book.stock === 0).length;

    main.querySelector('#adminKpis').innerHTML = [
      kpi(ICONS.book, 'Total titles', String(stats.total_books), 'in the catalog'),
      kpi(ICONS.box, 'Units in stock', String(stats.total_stock), 'across all titles'),
      kpi(ICONS.chart, 'Low stock', String(low.length), '10 units or fewer'),
      kpi(ICONS.close, 'Out of stock', String(out), 'needs restocking'),
      kpi(ICONS.receipt, 'Inventory value', money(stats.inventory_value), 'retail value on hand'),
    ].join('');

    const lowNode = main.querySelector('#lowStock');
    lowNode.innerHTML = low.length
      ? `<div class="table-wrap"><table class="data-table compact">
          <thead><tr><th>Product</th><th>Category</th><th>Stock</th><th>Status</th></tr></thead>
          <tbody>${low
            .slice(0, 6)
            .map(
              (book) => `<tr>
                <td><div class="cell-product">${thumb(book)}<div><strong>${esc(book.title)}</strong><span class="muted">#${book.id} · ${esc(book.author)}</span></div></div></td>
                <td>${esc(categoryName(book.category))}</td>
                <td>${book.stock}</td>
                <td>${stockPill(book.stock)}</td>
              </tr>`,
            )
            .join('')}</tbody>
        </table></div>`
      : emptyView('Everything is stocked', 'No title is below the low-stock threshold.');

    const ordersNode = main.querySelector('#recentOrders');
    ordersNode.innerHTML = orders.length
      ? `<div class="table-wrap"><table class="data-table compact">
          <thead><tr><th>Order</th><th>Customer</th><th>Total</th><th>Status</th></tr></thead>
          <tbody>${orders
            .map(
              (order) => `<tr>
                <td><strong>#${order.id}</strong><span class="muted block">${esc(formatDate(order.created_at))}</span></td>
                <td>${esc(order.customer_name)}</td>
                <td>${money(order.total)}</td>
                <td>${statusPill(order.status)}</td>
              </tr>`,
            )
            .join('')}</tbody>
        </table></div>`
      : emptyView('No orders yet', 'Orders placed in the store will appear here.');
  } catch (error) {
    main.querySelector('#adminKpis').innerHTML = '';
    main.querySelector('#lowStock').innerHTML = errorView(error.message);
    main.querySelector('#recentOrders').innerHTML = '';
  }
}

export async function renderAdminBooks(main) {
  main.innerHTML = `
    <div class="admin-page">
      <div class="admin-toolbar">
        <label class="field search-field"><span class="sr-only">Search books</span><input id="adminBookSearch" type="search" placeholder="Search by title or author…"></label>
        <label class="field"><span class="sr-only">Category</span><select id="adminCategoryFilter"><option value="">All categories</option></select></label>
        <button class="btn" id="addBookBtn" type="button">${ICONS.plus}<span>Add book</span></button>
      </div>
      <div class="panel">
        <div id="adminBooksTable"><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line"></div></div>
        <nav class="pagination" id="adminBooksPagination"></nav>
      </div>
    </div>`;

  const tableNode = main.querySelector('#adminBooksTable');
  const pagination = main.querySelector('#adminBooksPagination');
  const searchInput = main.querySelector('#adminBookSearch');
  const categoryFilter = main.querySelector('#adminCategoryFilter');
  const state = { books: [], categories: [], q: '', category: '', page: 1 };
  const PAGE_SIZE = 10;

  async function loadData() {
    try {
      const [books, categories] = await Promise.all([fetchAllBooks(), api.categories()]);
      state.books = books;
      state.categories = categories;
      categoryFilter.innerHTML =
        '<option value="">All categories</option>' +
        categories
          .map((category) => `<option value="${esc(category.code)}">${esc(category.name)}</option>`)
          .join('');
      categoryFilter.value = state.category;
      renderTable();
    } catch (error) {
      tableNode.innerHTML = errorView(error.message);
      tableNode.querySelector('[data-retry]')?.addEventListener('click', loadData);
    }
  }

  function filtered() {
    const query = state.q.toLowerCase();
    return state.books.filter(
      (book) =>
        (!state.category || book.category === state.category) &&
        (!query ||
          book.title.toLowerCase().includes(query) ||
          book.author.toLowerCase().includes(query) ||
          String(book.id) === query),
    );
  }

  function renderTable() {
    const rows = filtered();
    const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
    state.page = Math.min(state.page, pages);
    const visible = rows.slice((state.page - 1) * PAGE_SIZE, state.page * PAGE_SIZE);

    tableNode.innerHTML = visible.length
      ? `<div class="table-wrap"><table class="data-table">
          <thead><tr><th>Product</th><th>Author</th><th>Category</th><th>Stock</th><th>Price</th><th>Status</th><th class="actions-col">Actions</th></tr></thead>
          <tbody>${visible
            .map(
              (book) => `<tr data-row="${book.id}">
                <td><div class="cell-product">${thumb(book)}<div><strong>${esc(book.title)}</strong><span class="muted">#${book.id}</span></div></div></td>
                <td>${esc(book.author)}</td>
                <td>${esc(categoryName(book.category))}</td>
                <td>${book.stock}</td>
                <td>${money(book.price)}</td>
                <td>${stockPill(book.stock)}</td>
                <td class="actions-col">
                  <button class="icon-btn" type="button" data-edit="${book.id}" aria-label="Edit ${esc(book.title)}">${ICONS.edit}</button>
                  <button class="icon-btn danger" type="button" data-delete="${book.id}" aria-label="Delete ${esc(book.title)}">${ICONS.trash}</button>
                </td>
              </tr>`,
            )
            .join('')}</tbody>
        </table></div>`
      : emptyView('No books match', 'Adjust the search or category filter.');

    pagination.innerHTML = pages > 1
      ? `<span class="muted">Page ${state.page} of ${pages} · ${rows.length} books</span>
         <button class="page-btn" type="button" data-admin-page="${state.page - 1}" ${state.page === 1 ? 'disabled' : ''}>Previous</button>
         <button class="page-btn" type="button" data-admin-page="${state.page + 1}" ${state.page === pages ? 'disabled' : ''}>Next</button>`
      : `<span class="muted">${rows.length} book${rows.length === 1 ? '' : 's'}</span>`;
  }

  pagination.addEventListener('click', (event) => {
    const button = event.target.closest('[data-admin-page]');
    if (!button || button.disabled) return;
    state.page = Number(button.dataset.adminPage);
    renderTable();
  });

  tableNode.addEventListener('click', async (event) => {
    const edit = event.target.closest('[data-edit]');
    const remove = event.target.closest('[data-delete]');
    if (edit) {
      const book = state.books.find((item) => item.id === Number(edit.dataset.edit));
      if (book) openBookModal(book, state.categories, loadData);
    }
    if (remove) {
      const book = state.books.find((item) => item.id === Number(remove.dataset.delete));
      if (!book) return;
      if (!window.confirm(`Delete “${book.title}” from the catalog?`)) return;
      try {
        await api.admin.deleteBook(book.id);
        toast('Book deleted', 'success');
        await loadData();
      } catch (error) {
        toast(error.message, 'error');
      }
    }
  });

  searchInput.addEventListener(
    'input',
    debounce(() => {
      state.q = searchInput.value.trim();
      state.page = 1;
      renderTable();
    }),
  );

  categoryFilter.addEventListener('change', () => {
    state.category = categoryFilter.value;
    state.page = 1;
    renderTable();
  });

  main.querySelector('#addBookBtn').addEventListener('click', () => {
    if (!state.categories.length) return;
    openBookModal(null, state.categories, loadData);
  });

  await loadData();
}

function openBookModal(book, categories, onSaved) {
  const isEdit = Boolean(book);
  const body = `<form id="bookForm" class="form">
    <div class="form-grid">
      <label class="span-2">Title<input name="title" required maxlength="255" value="${esc(book?.title || '')}"></label>
      <label>Author<input name="author" required maxlength="150" value="${esc(book?.author || '')}"></label>
      <label>Category<select name="category" required>
        ${categories.map((category) => `<option value="${esc(category.code)}" ${book?.category === category.code ? 'selected' : ''}>${esc(category.name)}</option>`).join('')}
      </select></label>
      <label>Price (USD)<input name="price" type="number" min="0.01" step="0.01" required value="${book ? Number(book.price).toFixed(2) : '19.99'}"></label>
      <label>Stock<input name="stock" type="number" min="0" step="1" required value="${book ? book.stock : 12}"></label>
      <label class="span-2">Cover path<input name="cover" maxlength="255" placeholder="/static/covers/book-001.svg" value="${esc(book?.cover || '/static/covers/book-001.svg')}"></label>
      <label class="span-2">Description<textarea name="description" rows="4" maxlength="2000">${esc(book?.description || '')}</textarea></label>
      <p class="form-error span-2" id="bookFormError" hidden></p>
      <div class="modal-actions span-2">
        <button class="btn ghost" type="button" data-modal-close>Cancel</button>
        <button class="btn" type="submit">${isEdit ? 'Save changes' : 'Create book'}</button>
      </div>
    </div>
  </form>`;

  openModal({
    title: isEdit ? `Edit book #${book.id}` : 'Add a book',
    body,
    onMount(modal, close) {
      const form = modal.querySelector('#bookForm');
      const errorNode = modal.querySelector('#bookFormError');
      form.addEventListener('submit', async (event) => {
        event.preventDefault();
        errorNode.hidden = true;
        const payload = {
          title: form.title.value.trim(),
          author: form.author.value.trim(),
          category: form.category.value,
          description: form.description.value.trim(),
          price: Number(form.price.value),
          stock: Number(form.stock.value),
          cover: form.cover.value.trim(),
        };
        const button = form.querySelector('button[type="submit"]');
        button.disabled = true;
        try {
          if (isEdit) await api.admin.updateBook(book.id, payload);
          else await api.admin.createBook(payload);
          close();
          toast(isEdit ? 'Book updated' : 'Book created', 'success');
          onSaved();
        } catch (error) {
          errorNode.textContent = error.message;
          errorNode.hidden = false;
        } finally {
          button.disabled = false;
        }
      });
    },
  });
}

export async function renderAdminOrders(main) {
  main.innerHTML = `
    <div class="admin-page">
      <div class="admin-toolbar">
        <label class="field"><span class="sr-only">Status</span><select id="orderStatusFilter">
          <option value="">All statuses</option>
          ${STATUSES.map((status) => `<option value="${status}">${status}</option>`).join('')}
        </select></label>
        <button class="btn ghost" id="refreshOrders" type="button">Refresh</button>
      </div>
      <div class="panel"><div id="adminOrdersTable"><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line"></div></div></div>
    </div>`;

  const tableNode = main.querySelector('#adminOrdersTable');
  const statusFilter = main.querySelector('#orderStatusFilter');

  async function load() {
    tableNode.innerHTML = '<div class="skeleton skeleton-line"></div>';
    try {
      const orders = await api.admin.orders({ status: statusFilter.value || undefined, limit: 100 });
      if (!orders.length) {
        tableNode.innerHTML = emptyView('No orders', 'Orders will appear here after customers check out.');
        return;
      }
      tableNode.innerHTML = `<div class="table-wrap"><table class="data-table">
        <thead><tr><th>Order</th><th>Customer</th><th>Items</th><th>Total</th><th>Placed</th><th>Status</th><th>Update</th></tr></thead>
        <tbody>${orders
          .map((order) => {
            const next = NEXT_STATUS[order.status] || [];
            return `<tr>
              <td><strong>#${order.id}</strong></td>
              <td><div><strong>${esc(order.customer_name)}</strong><span class="muted block">${esc(order.customer_email)}</span></div></td>
              <td>${order.item_count}</td>
              <td>${money(order.total)}</td>
              <td>${esc(formatDate(order.created_at))}</td>
              <td>${statusPill(order.status)}</td>
              <td>${
                next.length
                  ? `<select class="status-select" data-order="${order.id}">
                      <option value="">Move to…</option>
                      ${next.map((status) => `<option value="${status}">${status}</option>`).join('')}
                    </select>`
                  : '<span class="muted">—</span>'
              }</td>
            </tr>`;
          })
          .join('')}</tbody>
      </table></div>`;
    } catch (error) {
      tableNode.innerHTML = errorView(error.message);
      tableNode.querySelector('[data-retry]')?.addEventListener('click', load);
    }
  }

  tableNode.addEventListener('change', async (event) => {
    const select = event.target.closest('[data-order]');
    if (!select || !select.value) return;
    select.disabled = true;
    try {
      await api.admin.updateOrderStatus(Number(select.dataset.order), select.value);
      toast(`Order #${select.dataset.order} marked ${select.value}`, 'success');
      await load();
    } catch (error) {
      toast(error.message, 'error');
      select.value = '';
      select.disabled = false;
    }
  });

  statusFilter.addEventListener('change', load);
  main.querySelector('#refreshOrders').addEventListener('click', load);
  await load();
}

export async function renderAdminCustomers(main) {
  main.innerHTML = `
    <div class="admin-page">
      <div class="panel">
        <header class="panel-head"><h2>Customers &amp; users</h2><span class="muted" id="customerCount"></span></header>
        <div id="adminCustomersTable"><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line"></div></div>
      </div>
    </div>`;

  const tableNode = main.querySelector('#adminCustomersTable');

  async function load() {
    try {
      const users = await api.admin.users();
      main.querySelector('#customerCount').textContent = `${users.length} accounts`;
      tableNode.innerHTML = `<div class="table-wrap"><table class="data-table">
        <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Joined</th></tr></thead>
        <tbody>${users
          .map(
            (user) => `<tr>
              <td><strong>${esc(user.name)}</strong></td>
              <td>${esc(user.email)}</td>
              <td><select class="role-select" data-user="${user.id}">
                <option value="customer" ${user.role === 'customer' ? 'selected' : ''}>customer</option>
                <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>admin</option>
              </select></td>
              <td>${user.is_active ? '<span class="pill status-completed">Active</span>' : '<span class="pill status-cancelled">Inactive</span>'}</td>
              <td>${esc(formatDate(user.created_at))}</td>
            </tr>`,
          )
          .join('')}</tbody>
      </table></div>`;
    } catch (error) {
      tableNode.innerHTML = errorView(error.message);
      tableNode.querySelector('[data-retry]')?.addEventListener('click', load);
    }
  }

  tableNode.addEventListener('change', async (event) => {
    const select = event.target.closest('[data-user]');
    if (!select) return;
    select.disabled = true;
    try {
      await api.admin.updateRole(Number(select.dataset.user), select.value);
      toast('Role updated', 'success');
    } catch (error) {
      toast(error.message, 'error');
    } finally {
      await load();
    }
  });

  await load();
}
