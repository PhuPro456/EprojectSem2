import { api } from '../api.js';
import {
  bookCard,
  categoryName,
  debounce,
  emptyView,
  errorView,
  esc,
  skeletonGrid,
} from '../ui.js';

const PAGE_SIZE = 12;
const SORTS = {
  id_asc: { sort_by: 'id', order: 'asc' },
  price_asc: { sort_by: 'price', order: 'asc' },
  price_desc: { sort_by: 'price', order: 'desc' },
  title_asc: { sort_by: 'title', order: 'asc' },
  stock_desc: { sort_by: 'stock', order: 'desc' },
};

function readQuery() {
  const raw = (location.hash || '').split('?')[1] || '';
  const params = new URLSearchParams(raw);
  return {
    q: params.get('q') || '',
    category: params.get('category') || '',
    sort: SORTS[params.get('sort')] ? params.get('sort') : 'id_asc',
    availability: params.get('availability') || '',
    page: Math.max(1, Number(params.get('page')) || 1),
  };
}

function writeQuery(filters) {
  const params = new URLSearchParams();
  if (filters.q) params.set('q', filters.q);
  if (filters.category) params.set('category', filters.category);
  if (filters.sort !== 'id_asc') params.set('sort', filters.sort);
  if (filters.availability) params.set('availability', filters.availability);
  if (filters.page > 1) params.set('page', String(filters.page));
  const query = params.toString();
  history.replaceState(null, '', `#/catalog${query ? `?${query}` : ''}`);
}

export async function renderCatalog(main) {
  const filters = readQuery();

  main.innerHTML = `
    <div class="page catalog-page">
      <header class="catalog-head">
        <div>
          <p class="eyebrow">The collection</p>
          <h1>${filters.category ? esc(categoryName(filters.category)) : 'All books'}</h1>
        </div>
        <p class="results-count" id="resultCount" aria-live="polite">Loading…</p>
      </header>
      <div class="catalog-controls">
        <label class="field search-field">
          <span class="sr-only">Search books</span>
          <input id="searchInput" type="search" placeholder="Search titles or authors…" autocomplete="off" value="${esc(filters.q)}">
        </label>
        <label class="field">
          <span class="sr-only">Category</span>
          <select id="categorySelect"><option value="">All categories</option></select>
        </label>
        <label class="field">
          <span class="sr-only">Availability</span>
          <select id="availabilitySelect">
            <option value="">Any availability</option>
            <option value="true">In stock</option>
            <option value="false">Out of stock</option>
          </select>
        </label>
        <label class="field">
          <span class="sr-only">Sort</span>
          <select id="sortSelect">
            <option value="id_asc">Featured</option>
            <option value="price_asc">Price: low to high</option>
            <option value="price_desc">Price: high to low</option>
            <option value="title_asc">Title: A–Z</option>
            <option value="stock_desc">Stock: high to low</option>
          </select>
        </label>
        <button class="btn ghost" id="clearFilters" type="button">Clear</button>
      </div>
      <div id="catalogGrid">${skeletonGrid(PAGE_SIZE)}</div>
      <nav class="pagination" id="pagination" aria-label="Pagination"></nav>
    </div>`;

  const grid = main.querySelector('#catalogGrid');
  const pagination = main.querySelector('#pagination');
  const resultCount = main.querySelector('#resultCount');
  const searchInput = main.querySelector('#searchInput');
  const categorySelect = main.querySelector('#categorySelect');
  const availabilitySelect = main.querySelector('#availabilitySelect');
  const sortSelect = main.querySelector('#sortSelect');

  availabilitySelect.value = filters.availability;
  sortSelect.value = filters.sort;

  const categories = await api.categories().catch(() => []);
  categorySelect.innerHTML =
    '<option value="">All categories</option>' +
    categories
      .map(
        (category) =>
          `<option value="${esc(category.code)}">${esc(category.name)} (${category.book_count})</option>`,
      )
      .join('');
  categorySelect.value = filters.category;

  async function load() {
    writeQuery(filters);
    grid.innerHTML = skeletonGrid(PAGE_SIZE);
    pagination.innerHTML = '';
    resultCount.textContent = 'Loading…';
    const sort = SORTS[filters.sort] || SORTS.id_asc;
    try {
      const data = await api.listBooks({
        skip: (filters.page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
        keyword: filters.q || undefined,
        category: filters.category || undefined,
        is_available:
          filters.availability === '' ? undefined : filters.availability === 'true',
        sort_by: sort.sort_by,
        order: sort.order,
      });

      if (!data.items.length) {
        grid.innerHTML = emptyView(
          'No books found',
          'Try a different search, category, or availability filter.',
          '<button class="btn ghost" type="button" data-clear-inline>Clear filters</button>',
        );
        const clear = grid.querySelector('[data-clear-inline]');
        if (clear) clear.addEventListener('click', clearFilters);
      } else {
        grid.innerHTML = `<div class="book-grid">${data.items.map(bookCard).join('')}</div>`;
      }
      resultCount.textContent = `${data.total} book${data.total === 1 ? '' : 's'}`;
      renderPagination(data.total);
      const heading = main.querySelector('.catalog-head h1');
      if (heading) heading.textContent = filters.category ? categoryName(filters.category) : 'All books';
    } catch (error) {
      resultCount.textContent = 'Unavailable';
      grid.innerHTML = errorView(error.message);
      grid.querySelector('[data-retry]')?.addEventListener('click', load);
    }
  }

  function renderPagination(total) {
    const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    if (pages <= 1) {
      pagination.innerHTML = '';
      return;
    }
    const current = Math.min(filters.page, pages);
    const numbers = [];
    const start = Math.max(1, current - 2);
    const end = Math.min(pages, start + 4);
    for (let page = start; page <= end; page += 1) numbers.push(page);

    pagination.innerHTML = `
      <button type="button" class="page-btn" data-page="${current - 1}" ${current === 1 ? 'disabled' : ''}>Previous</button>
      ${start > 1 ? `<button type="button" class="page-btn" data-page="1">1</button>${start > 2 ? '<span class="page-ellipsis">…</span>' : ''}` : ''}
      ${numbers.map((page) => `<button type="button" class="page-btn ${page === current ? 'active' : ''}" data-page="${page}">${page}</button>`).join('')}
      ${end < pages ? `${end < pages - 1 ? '<span class="page-ellipsis">…</span>' : ''}<button type="button" class="page-btn" data-page="${pages}">${pages}</button>` : ''}
      <button type="button" class="page-btn" data-page="${current + 1}" ${current === pages ? 'disabled' : ''}>Next</button>`;
  }

  pagination.addEventListener('click', (event) => {
    const button = event.target.closest('[data-page]');
    if (!button || button.disabled) return;
    filters.page = Number(button.dataset.page);
    load();
    main.querySelector('.catalog-head')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  searchInput.addEventListener(
    'input',
    debounce(() => {
      filters.q = searchInput.value.trim();
      filters.page = 1;
      load();
    }),
  );

  categorySelect.addEventListener('change', () => {
    filters.category = categorySelect.value;
    filters.page = 1;
    load();
  });

  availabilitySelect.addEventListener('change', () => {
    filters.availability = availabilitySelect.value;
    filters.page = 1;
    load();
  });

  sortSelect.addEventListener('change', () => {
    filters.sort = sortSelect.value;
    filters.page = 1;
    load();
  });

  function clearFilters() {
    filters.q = '';
    filters.category = '';
    filters.availability = '';
    filters.sort = 'id_asc';
    filters.page = 1;
    searchInput.value = '';
    categorySelect.value = '';
    availabilitySelect.value = '';
    sortSelect.value = 'id_asc';
    load();
  }

  main.querySelector('#clearFilters').addEventListener('click', clearFilters);
  await load();
}
