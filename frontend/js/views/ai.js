import { api } from '../api.js';
import { state } from '../store.js';
import { ICONS, bookCard, errorView, esc, money, toast } from '../ui.js';

const GREETING =
  "Hello! I'm the Bookstore Pro assistant. Tell me a genre, a mood, or a budget and I'll pull a few titles from the shelf.";
const DEFAULT_CHIPS = [
  'A cozy mystery',
  'Science fiction under $20',
  'A romance to get lost in',
  'Staff picks',
];

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function chatBooks(books) {
  if (!books.length) return '';
  return `<div class="chat-books">${books
    .map(
      (book) => `<a class="chat-book" href="#/book/${book.id}">
        <img src="${esc(book.cover)}" alt="" loading="lazy">
        <span><strong>${esc(book.title)}</strong><small>${esc(book.author)} · ${money(book.price)}</small></span>
      </a>`,
    )
    .join('')}</div>`;
}

function messageNode(role, text, books = []) {
  const wrap = document.createElement('div');
  wrap.className = `chat-msg ${role}`;
  wrap.innerHTML = `<div class="chat-bubble"><p>${esc(text)}</p>${chatBooks(books)}</div>`;
  return wrap;
}

function renderChips(container, chips, onPick) {
  container.innerHTML = chips
    .map(
      (chip) => `<button class="chip" type="button" data-chip="${esc(chip)}">${esc(chip)}</button>`,
    )
    .join('');
  container.querySelectorAll('[data-chip]').forEach((button) => {
    button.addEventListener('click', () => onPick(button.dataset.chip));
  });
}

export async function renderAi(main) {
  main.innerHTML = `
    <div class="page ai-page">
      <header class="ai-head">
        <div>
          <p class="eyebrow">${ICONS.spark} AI reading room</p>
          <h1>Your next read,<br><em>in conversation.</em></h1>
          <p class="muted">A local bookseller assistant with the catalog, stock levels and reader history at hand. No external AI service is called — it works offline.</p>
        </div>
        <div class="ai-badges">
          <span class="ai-badge">Catalogue-aware</span>
          <span class="ai-badge">Sentiment-labelled reviews</span>
          <span class="ai-badge">Bring your own key</span>
        </div>
      </header>

      <div class="ai-layout">
        <section class="chat-card">
          <header class="chat-head">
            <div class="chat-avatar">${ICONS.spark}</div>
            <div><strong>Bookstore assistant</strong><span class="muted">Usually replies instantly</span></div>
          </header>
          <div class="chat-messages" id="aiMessages"></div>
          <div class="chat-chips" id="aiChips"></div>
          <form class="ai-composer" id="aiForm">
            <label class="sr-only" for="aiInput">Ask for a recommendation</label>
            <input id="aiInput" name="message" maxlength="500" autocomplete="off" placeholder="e.g. a gripping mystery under $18">
            <button class="btn" type="submit">Send</button>
          </form>
          <p class="ai-note">Deterministic local recommender — no messages leave this server.</p>
        </section>

        <aside class="ai-side">
          <section class="panel ai-keys" id="aiKeys">
            <div class="skeleton skeleton-line"></div>
            <div class="skeleton skeleton-line short"></div>
          </section>
          <section class="panel ai-about">
            <header class="panel-head"><h2>How it works</h2></header>
            <ul class="ai-steps">
              <li><span>01</span> Reads the live catalog, stock and your order history.</li>
              <li><span>02</span> Matches genres, budgets and reader favourites.</li>
              <li><span>03</span> Suggests three titles you can add to your cart.</li>
            </ul>
          </section>
        </aside>
      </div>

      <section class="ai-recs" id="aiRecs">
        <div class="section-head">
          <div><p class="eyebrow">Picked for you</p><h2>Fresh from the shelves</h2></div>
        </div>
        <div class="skeleton-grid">${'<div class="skeleton skeleton-line"></div>'.repeat(3)}</div>
      </section>
    </div>`;

  const messages = main.querySelector('#aiMessages');
  const chips = main.querySelector('#aiChips');
  const form = main.querySelector('#aiForm');
  const input = main.querySelector('#aiInput');
  const keysNode = main.querySelector('#aiKeys');
  const recsNode = main.querySelector('#aiRecs');

  messages.appendChild(messageNode('assistant', GREETING));

  function scrollChat() {
    messages.scrollTop = messages.scrollHeight;
  }

  async function send(text) {
    const message = text.trim();
    if (!message) return;
    messages.appendChild(messageNode('user', message));
    input.value = '';
    const typing = messageNode('assistant', 'Checking the shelves…');
    typing.classList.add('typing');
    messages.appendChild(typing);
    scrollChat();

    try {
      const data = await api.ai.chat(message);
      typing.remove();
      messages.appendChild(messageNode('assistant', data.reply, data.books));
      renderChips(chips, data.suggestions.length ? data.suggestions : DEFAULT_CHIPS, send);
      scrollChat();
    } catch (error) {
      typing.remove();
      messages.appendChild(messageNode('assistant', error.message));
      scrollChat();
    }
  }

  function pick(text) {
    send(text);
    input.focus();
  }

  renderChips(chips, DEFAULT_CHIPS, pick);

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    send(input.value);
  });

  const providersPromise = api.ai.providers().catch(() => []);
  loadRecommendations(recsNode);
  renderKeys(keysNode, providersPromise);
}

async function loadRecommendations(node) {
  node.innerHTML = `<div class="section-head">
      <div><p class="eyebrow">Picked for you</p><h2>Fresh from the shelves</h2></div>
    </div><div class="book-grid">${'<div class="book-card skeleton-card"><div class="skeleton skeleton-cover"></div><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line short"></div></div>'.repeat(4)}</div>`;
  try {
    const data = await api.ai.recommendations(4);
    node.innerHTML = `<div class="section-head">
      <div><p class="eyebrow">Picked for you</p><h2>${esc(data.reason)}</h2></div>
      <a class="link-arrow" href="#/catalog">Browse everything <span aria-hidden="true">→</span></a>
    </div>
    <div class="book-grid">${data.items.map(bookCard).join('')}</div>`;
  } catch (error) {
    node.innerHTML = errorView(error.message);
    node.querySelector('[data-retry]')?.addEventListener('click', () => loadRecommendations(node));
  }
}

async function renderKeys(node, providersPromise) {
  if (!state.user) {
    node.innerHTML = `<header class="panel-head"><h2>Bring your own AI key</h2></header>
      <p class="muted">Sign in to store provider keys encrypted at rest. The assistant itself never needs one.</p>
      <a class="btn full" href="#/login">Sign in to add a key</a>`;
    return;
  }

  node.innerHTML = `<header class="panel-head"><h2>Your AI keys</h2><span class="muted" id="keyCount"></span></header>
    <div id="keyBody"><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line short"></div></div>`;

  const body = node.querySelector('#keyBody');
  const providers = await providersPromise;

  async function load() {
    try {
      const keys = await api.ai.keys();
      node.querySelector('#keyCount').textContent = `${keys.length} stored`;
      body.innerHTML = `${keyForm(providers)}${keyList(keys, providers)}`;
      bindForm(body, providers, load);
    } catch (error) {
      body.innerHTML = errorView(error.message);
      body.querySelector('[data-retry]')?.addEventListener('click', load);
    }
  }

  body.addEventListener('click', (event) => handleKeyClick(event, body, load));
  await load();
}

function providerOptions(providers, selected) {
  return providers
    .map(
      (provider) =>
        `<option value="${esc(provider.slug)}" ${provider.slug === selected ? 'selected' : ''}>${esc(provider.name)}</option>`,
    )
    .join('');
}

function keyForm(providers) {
  const first = providers[0];
  return `<form class="key-form" id="keyForm">
    <label class="field"><span>Provider</span><select name="provider">${providerOptions(providers, first?.slug)}</select></label>
    <label class="field"><span>Label</span><input name="label" maxlength="80" placeholder="Personal key" required></label>
    <label class="field"><span>API key</span><input name="api_key" type="password" autocomplete="off" minlength="20" maxlength="512" placeholder="${esc(first?.key_prefix || 'sk-')}…" required></label>
    <p class="key-hint" id="keyHint">${esc(first ? `${first.name} keys start with ${first.key_prefix}` : 'Choose a provider')}</p>
    <p class="form-error" id="keyError" hidden></p>
    <button class="btn full" type="submit">Save encrypted key</button>
  </form>`;
}

function keyList(keys, providers) {
  if (!keys.length) {
    return `<p class="key-empty muted">No keys yet. Keys are encrypted with the server secret before they are stored.</p>`;
  }
  const names = Object.fromEntries(providers.map((provider) => [provider.slug, provider.name]));
  return `<ul class="key-list">${keys
    .map(
      (key) => `<li class="key-item">
        <div class="key-main">
          <span class="key-provider">${esc(names[key.provider] || key.provider)}</span>
          <strong>${esc(key.label)}</strong>
          <span class="key-meta"><code>${esc(key.key_hint)}</code> · added ${esc(formatDate(key.created_at))}</span>
        </div>
        <div class="key-actions">
          <button class="btn ghost tiny" type="button" data-verify-key="${key.id}">Verify</button>
          <button class="icon-btn danger" type="button" data-delete-key="${key.id}" aria-label="Delete key">${ICONS.trash}</button>
        </div>
        <p class="key-status" data-key-status="${key.id}" hidden></p>
      </li>`,
    )
    .join('')}</ul>`;
}

function bindForm(body, providers, reload) {
  const form = body.querySelector('#keyForm');
  const errorNode = body.querySelector('#keyError');
  const hint = body.querySelector('#keyHint');

  form.provider.addEventListener('change', () => {
    const provider = providers.find((entry) => entry.slug === form.provider.value);
    hint.textContent = provider
      ? `${provider.name} keys start with ${provider.key_prefix}`
      : 'Choose a provider';
    form.api_key.placeholder = provider ? `${provider.key_prefix}…` : 'sk-…';
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorNode.hidden = true;
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      await api.ai.createKey({
        provider: form.provider.value,
        label: form.label.value.trim(),
        api_key: form.api_key.value.trim(),
      });
      toast('AI key saved', 'success');
      await reload();
    } catch (error) {
      errorNode.textContent = error.message;
      errorNode.hidden = false;
    } finally {
      button.disabled = false;
    }
  });
}

async function handleKeyClick(event, body, reload) {
  const verify = event.target.closest('[data-verify-key]');
  if (verify) {
    verify.disabled = true;
    const status = body.querySelector(`[data-key-status="${verify.dataset.verifyKey}"]`);
    try {
      const result = await api.ai.verifyKey(Number(verify.dataset.verifyKey));
      if (status) {
        status.hidden = false;
        status.textContent = result.message;
        status.className = `key-status ${result.status === 'format_ok' ? 'ok' : 'bad'}`;
      }
      toast(result.message, result.status === 'format_ok' ? 'success' : 'error');
    } catch (error) {
      toast(error.message, 'error');
    } finally {
      verify.disabled = false;
    }
    return;
  }

  const remove = event.target.closest('[data-delete-key]');
  if (!remove) return;
  if (!window.confirm('Delete this AI key?')) return;
  try {
    await api.ai.deleteKey(Number(remove.dataset.deleteKey));
    toast('AI key deleted', 'success');
    await reload();
  } catch (error) {
    toast(error.message, 'error');
  }
}
