import { api } from './api.js';

const TOKEN_KEY = 'bookstore.token';
const CART_KEY = 'bookstore.cart';

export const state = {
  token: localStorage.getItem(TOKEN_KEY),
  user: null,
  cart: readCart(),
};

const listeners = new Set();

export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function emit(event) {
  listeners.forEach((listener) => listener(state, event));
}

function readCart() {
  try {
    const parsed = JSON.parse(localStorage.getItem(CART_KEY) || '[]');
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function persistCart() {
  localStorage.setItem(CART_KEY, JSON.stringify(state.cart));
}

export function setToken(token) {
  state.token = token;
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export async function loadUser() {
  if (!state.token) {
    state.user = null;
    return null;
  }
  try {
    state.user = await api.me();
  } catch {
    setToken(null);
    state.user = null;
  }
  emit('auth');
  return state.user;
}

export function logout() {
  setToken(null);
  state.user = null;
  emit('auth');
}

export function isAdmin() {
  return state.user?.role === 'admin';
}

export function cartCount() {
  return state.cart.reduce((sum, item) => sum + item.quantity, 0);
}

export function cartTotal() {
  return state.cart.reduce((sum, item) => sum + item.quantity * item.price, 0);
}

export function cartAdd(book, quantity = 1) {
  const existing = state.cart.find((item) => item.book_id === book.id);
  const stock = Number(book.stock) || 0;
  if (stock <= 0) return { added: false, limited: false };
  if (existing) {
    const next = Math.min(existing.quantity + quantity, stock);
    const limited = next < existing.quantity + quantity;
    existing.quantity = next;
    existing.stock = stock;
    persistCart();
    emit('cart');
    return { added: next > existing.quantity - quantity, limited };
  }
  const next = Math.min(quantity, stock);
  state.cart.push({
    book_id: book.id,
    title: book.title,
    author: book.author,
    price: Number(book.price),
    cover: book.cover,
    stock,
    quantity: next,
  });
  persistCart();
  emit('cart');
  return { added: true, limited: next < quantity };
}

export function cartSetQuantity(bookId, quantity) {
  const item = state.cart.find((entry) => entry.book_id === bookId);
  if (!item) return;
  if (quantity <= 0) {
    state.cart = state.cart.filter((entry) => entry.book_id !== bookId);
  } else {
    item.quantity = Math.min(quantity, item.stock || quantity);
  }
  persistCart();
  emit('cart');
}

export function cartRemove(bookId) {
  state.cart = state.cart.filter((item) => item.book_id !== bookId);
  persistCart();
  emit('cart');
}

export function cartClear() {
  state.cart = [];
  persistCart();
  emit('cart');
}
