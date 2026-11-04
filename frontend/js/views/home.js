import { api } from '../api.js';
import { bookCard, categoryName, errorView, esc, skeletonGrid } from '../ui.js';

const TINTS = ['#e7edf7', '#f6ede1', '#e9f0e4', '#efe7f3', '#f8e8e6', '#e6eff0'];

export async function renderHome(main) {
  main.innerHTML = `
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-copy">
          <p class="eyebrow">The reading room</p>
          <h1>Find your<br><em>next chapter.</em></h1>
          <p class="hero-lede">One hundred titles across fantasy, mystery, romance, fiction and science fiction — curated, in stock, and ready to ship.</p>
          <div class="hero-actions">
            <a class="btn" href="#/catalog">Shop all books</a>
            <a class="btn ghost" href="#/catalog?sort=price_asc">Browse under $15</a>
          </div>
          <dl class="hero-stats">
            <div><dt>100</dt><dd>curated titles</dd></div>
            <div><dt>5</dt><dd>genres</dd></div>
            <div><dt>$35</dt><dd>free shipping</dd></div>
          </dl>
        </div>
        <div class="hero-tiles" id="homeTiles">
          ${Array.from({ length: 3 }, () => '<div class="cat-tile skeleton-tile"></div>').join('')}
        </div>
      </div>
    </section>
    <section class="section">
      <div class="section-head">
        <div><p class="eyebrow">Staff shelves</p><h2>New &amp; noteworthy</h2></div>
        <a class="link-arrow" href="#/catalog">View all books <span aria-hidden="true">→</span></a>
      </div>
      <div id="homeGrid">${skeletonGrid(8)}</div>
    </section>
    <section class="band">
      <div class="band-item"><strong>Free shipping</strong><span>On every order over $35</span></div>
      <div class="band-item"><strong>30-day returns</strong><span>No questions asked</span></div>
      <div class="band-item"><strong>Secure checkout</strong><span>JWT-protected accounts</span></div>
    </section>
    <section class="section split">
      <div class="split-copy">
        <p class="eyebrow">The collection</p>
        <h2>Five shelves, one hundred stories</h2>
        <p class="muted">From doorstopper space operas to quiet domestic fiction, every title is a real published work with a demo price and stock level.</p>
        <a class="btn ghost" href="#/catalog">Browse the catalog</a>
      </div>
      <div class="split-list" id="homeCategories"></div>
    </section>`;

  const tiles = main.querySelector('#homeTiles');
  const grid = main.querySelector('#homeGrid');
  const list = main.querySelector('#homeCategories');

  try {
    const [categories, pageOne, pageTwo] = await Promise.all([
      api.categories(),
      api.listBooks({ limit: 50, skip: 0, sort_by: 'id', order: 'asc' }),
      api.listBooks({ limit: 50, skip: 50, sort_by: 'id', order: 'asc' }),
    ]);
    const books = [...pageOne.items, ...pageTwo.items];

    tiles.innerHTML = categories
      .map((category, index) => {
        const covers = books
          .filter((book) => book.category === category.code)
          .slice(0, 2);
        return `<a class="cat-tile" href="#/catalog?category=${encodeURIComponent(category.code)}" style="--tint:${TINTS[index % TINTS.length]}">
          <div class="cat-covers">
            ${covers.map((book, position) => `<img class="cover-${position}" src="${esc(book.cover)}" alt="" loading="lazy">`).join('')}
          </div>
          <div class="cat-meta"><span class="cat-name">${esc(category.name)}</span><span class="cat-count">${category.book_count} titles</span></div>
        </a>`;
      })
      .join('');

    const featured = books.slice(-8).reverse();
    grid.innerHTML = `<div class="book-grid">${featured.map(bookCard).join('')}</div>`;

    list.innerHTML = categories
      .map(
        (category) => `<a class="split-row" href="#/catalog?category=${encodeURIComponent(category.code)}">
          <span>${esc(category.name)}</span>
          <span class="muted">${category.book_count} books</span>
          <span aria-hidden="true">→</span>
        </a>`,
      )
      .join('');
  } catch (error) {
    grid.innerHTML = errorView(error.message);
    const retry = grid.querySelector('[data-retry]');
    if (retry) retry.addEventListener('click', () => renderHome(main));
    tiles.innerHTML = '';
    list.innerHTML = '';
  }
}
