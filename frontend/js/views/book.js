import { api } from '../api.js';
import { cartAdd, state } from '../store.js';
import {
  ICONS,
  bookCard,
  categoryName,
  esc,
  money,
  stockLabel,
  toast,
} from '../ui.js';

export async function renderBook(main, bookId) {
  main.innerHTML = `<div class="page"><div class="detail-skeleton"><div class="skeleton skeleton-cover tall"></div><div><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line tiny"></div></div></div></div>`;

  let book;
  try {
    book = await api.getBook(bookId);
  } catch (error) {
    const notFound = error.status === 404;
    main.innerHTML = `<div class="page"><div class="state-card">
      <h3>${notFound ? 'Book not found' : 'Could not load this book'}</h3>
      <p>${esc(notFound ? 'That title may have been removed from the catalog.' : error.message)}</p>
      <a class="btn" href="#/catalog">Back to the catalog</a>
    </div></div>`;
    return;
  }

  let related = [];
  try {
    const data = await api.listBooks({ category: book.category, limit: 5 });
    related = data.items.filter((item) => item.id !== book.id).slice(0, 4);
  } catch {
    related = [];
  }

  const maxQuantity = Math.max(0, book.stock);
  main.innerHTML = `
    <div class="page detail-page">
      <a class="back-link" href="#/catalog">${ICONS.arrowLeft} Back to catalog</a>
      <div class="detail">
        <div class="detail-cover">
          ${book.cover ? `<img src="${esc(book.cover)}" alt="Cover of ${esc(book.title)}">` : '<div class="cover-fallback">No cover</div>'}
        </div>
        <div class="detail-info">
          <a class="book-cat" href="#/catalog?category=${encodeURIComponent(book.category)}">${esc(categoryName(book.category))}</a>
          <h1>${esc(book.title)}</h1>
          <p class="detail-author">by ${esc(book.author)}</p>
          <p class="detail-desc">${esc(book.description)}</p>
          <div class="detail-buy">
            <span class="detail-price">${money(book.price)}</span>
            ${stockLabel(book.stock)}
          </div>
          <div class="detail-actions">
            <div class="qty" role="group" aria-label="Quantity">
              <button type="button" id="qtyMinus" aria-label="Decrease quantity">${ICONS.minus}</button>
              <span id="qtyValue">1</span>
              <button type="button" id="qtyPlus" aria-label="Increase quantity">${ICONS.plus}</button>
            </div>
            <button class="btn" id="addToCart" type="button" ${maxQuantity === 0 ? 'disabled' : ''}>
              ${maxQuantity === 0 ? 'Out of stock' : 'Add to cart'}
            </button>
          </div>
          <ul class="detail-facts">
            <li>Free standard shipping over $35</li>
            <li>30-day returns on every order</li>
            <li>Orders are stored in PostgreSQL</li>
          </ul>
        </div>
      </div>
      <section class="reviews">
        <div class="section-head">
          <div><p class="eyebrow">Reader voices</p><h2>Reviews</h2></div>
          <span class="muted" id="reviewSummaryText"></span>
        </div>
        <div id="reviewBody"><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line short"></div></div>
      </section>
      ${
        related.length
          ? `<section class="related">
              <div class="section-head"><div><p class="eyebrow">Keep browsing</p><h2>More in ${esc(categoryName(book.category))}</h2></div></div>
              <div class="book-grid">${related.map(bookCard).join('')}</div>
            </section>`
          : ''
      }
    </div>`;

  let quantity = maxQuantity > 0 ? 1 : 0;
  const qtyValue = main.querySelector('#qtyValue');
  const updateQty = () => {
    qtyValue.textContent = String(quantity);
  };
  main.querySelector('#qtyMinus').addEventListener('click', () => {
    quantity = Math.max(1, quantity - 1);
    updateQty();
  });
  main.querySelector('#qtyPlus').addEventListener('click', () => {
    quantity = Math.min(maxQuantity, quantity + 1);
    updateQty();
  });
  main.querySelector('#addToCart').addEventListener('click', () => {
    const result = cartAdd(book, quantity);
    if (!result.added) {
      toast('This title is out of stock', 'error');
      return;
    }
    toast(
      result.limited
        ? `Added ${quantity} — only ${maxQuantity} available`
        : `${quantity} × ${book.title} added to cart`,
      'success',
    );
  });

  loadReviews(main, book.id);
}

function stars(rating) {
  const filled = Math.max(0, Math.min(5, Number(rating) || 0));
  return `<span class="stars" aria-label="${filled} out of 5">${'★'.repeat(filled)}${'☆'.repeat(5 - filled)}</span>`;
}

function initials(name) {
  return String(name || '?')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('');
}

function summaryBar(kind, count, total) {
  const percent = total ? (count / total) * 100 : 0;
  return `<div class="review-bar-row">
    <span class="review-bar-label">${kind}</span>
    <div class="review-bar-track"><span class="review-bar-fill ${kind}" style="width:${percent.toFixed(1)}%"></span></div>
    <span class="review-bar-count">${count}</span>
  </div>`;
}

function reviewCard(review) {
  const date = new Date(review.created_at);
  const when = Number.isNaN(date.getTime())
    ? ''
    : date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  return `<article class="review-item">
    <header class="review-item-head">
      <div class="reviewer">
        <span class="avatar small">${esc(initials(review.author_name))}</span>
        <div><strong>${esc(review.author_name)}</strong><span class="muted">${esc(when)}</span></div>
      </div>
      <div class="review-rating">${stars(review.rating)}<span class="sentiment-pill ${esc(review.sentiment)}">${esc(review.sentiment)}</span></div>
    </header>
    <p class="review-text">${esc(review.text)}</p>
    ${
      review.keywords.length
        ? `<div class="review-keywords">${review.keywords
            .map((keyword) => `<span class="keyword-chip ${esc(review.sentiment)}">${esc(keyword)}</span>`)
            .join('')}</div>`
        : ''
    }
  </article>`;
}

async function loadReviews(main, bookId) {
  const node = main.querySelector('#reviewBody');
  if (!node) return;

  let data;
  try {
    data = await api.bookReviews(bookId);
  } catch (error) {
    node.innerHTML = `<p class="muted">Reviews are unavailable right now: ${esc(error.message)}</p>`;
    return;
  }

  const { summary, items } = data;
  const summaryText = main.querySelector('#reviewSummaryText');
  if (summaryText) {
    summaryText.textContent = summary.total
      ? `${summary.average_rating.toFixed(1)} average from ${summary.total} review${summary.total === 1 ? '' : 's'}`
      : 'No reviews yet';
  }

  const form = state.user
    ? `<form class="review-form" id="reviewForm">
        <header><h3>Share your thoughts</h3><p class="muted">Signed in as ${esc(state.user.name)}</p></header>
        <div class="form-grid review-form-grid">
          <label>Rating<select name="rating">
            ${[5, 4, 3, 2, 1].map((value) => `<option value="${value}" ${value === 5 ? 'selected' : ''}>${value} star${value === 1 ? '' : 's'}</option>`).join('')}
          </select></label>
          <label class="span-2">Your review<textarea name="text" rows="3" minlength="3" maxlength="2000" required placeholder="What worked, what didn't?"></textarea></label>
        </div>
        <p class="form-error" id="reviewError" hidden></p>
        <button class="btn" type="submit">Post review</button>
      </form>`
    : `<p class="review-signin"><a href="#/login" data-review-signin>Sign in</a> to leave a review.</p>`;

  node.innerHTML = `
    <div class="review-summary">
      <div class="review-score">
        <strong>${summary.total ? summary.average_rating.toFixed(1) : '—'}</strong>
        ${stars(Math.round(summary.average_rating))}
        <span class="muted">${summary.total} review${summary.total === 1 ? '' : 's'}</span>
      </div>
      <div class="review-bars">
        ${summaryBar('positive', summary.positive, summary.total)}
        ${summaryBar('neutral', summary.neutral, summary.total)}
        ${summaryBar('negative', summary.negative, summary.total)}
      </div>
    </div>
    <div class="review-list">
      ${items.length ? items.map(reviewCard).join('') : '<p class="muted review-empty">No one has reviewed this title yet.</p>'}
    </div>
    ${form}`;

  node.querySelector('[data-review-signin]')?.addEventListener('click', () => {
    sessionStorage.setItem('bookstore.next', location.hash || '#/');
  });

  const formNode = node.querySelector('#reviewForm');
  if (!formNode) return;
  formNode.addEventListener('submit', async (event) => {
    event.preventDefault();
    const errorNode = formNode.querySelector('#reviewError');
    errorNode.hidden = true;
    const button = formNode.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      await api.addReview(bookId, {
        rating: Number(formNode.rating.value),
        text: formNode.text.value.trim(),
      });
      toast('Review posted', 'success');
      await loadReviews(main, bookId);
    } catch (error) {
      errorNode.textContent = error.message;
      errorNode.hidden = false;
      button.disabled = false;
    }
  });
}
