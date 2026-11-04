const BASE = '/api/v1';
const TOKEN_KEY = 'bookstore.token';

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function authToken() {
  return localStorage.getItem(TOKEN_KEY);
}

async function request(path, { method = 'GET', json, form, anonymous = false } = {}) {
  const headers = { Accept: 'application/json' };
  if (json !== undefined) headers['Content-Type'] = 'application/json';
  if (form !== undefined) headers['Content-Type'] = 'application/x-www-form-urlencoded';
  const token = authToken();
  if (token && !anonymous) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(BASE + path, {
      method,
      headers,
      body:
        json !== undefined
          ? JSON.stringify(json)
          : form !== undefined
            ? new URLSearchParams(form)
            : undefined,
    });
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Is the backend running?');
  }

  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    let detail = data?.detail ?? data?.message;
    if (Array.isArray(detail)) detail = detail.map((item) => item.msg).join('; ');
    throw new ApiError(response.status, detail || `Request failed (${response.status})`);
  }
  return data;
}

function qs(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') query.set(key, value);
  });
  return query.toString();
}

export const api = {
  listBooks(params = {}) {
    const query = qs(params);
    return request(`/books${query ? `?${query}` : ''}`);
  },
  getBook(id) {
    return request(`/books/${id}`);
  },
  categories() {
    return request('/books/categories');
  },
  stats() {
    return request('/books/stats');
  },
  login(email, password) {
    return request('/auth/login', {
      method: 'POST',
      form: { username: email, password },
      anonymous: true,
    });
  },
  register(payload) {
    return request('/auth/register', { method: 'POST', json: payload, anonymous: true });
  },
  me() {
    return request('/auth/me');
  },
  myOrders() {
    return request('/orders');
  },
  checkout(items) {
    return request('/orders', { method: 'POST', json: { items } });
  },
  bookReviews(bookId) {
    return request(`/books/${bookId}/reviews`);
  },
  addReview(bookId, payload) {
    return request(`/books/${bookId}/reviews`, { method: 'POST', json: payload });
  },
  ai: {
    providers() {
      return request('/ai/providers', { anonymous: true });
    },
    recommendations(limit = 4) {
      return request(`/ai/recommendations?limit=${limit}`);
    },
    chat(message) {
      return request('/ai/chat', { method: 'POST', json: { message } });
    },
    keys() {
      return request('/ai/keys');
    },
    createKey(payload) {
      return request('/ai/keys', { method: 'POST', json: payload });
    },
    deleteKey(id) {
      return request(`/ai/keys/${id}`, { method: 'DELETE' });
    },
    verifyKey(id) {
      return request(`/ai/keys/${id}/verify`, { method: 'POST' });
    },
  },
  admin: {
    orders(params = {}) {
      const query = qs(params);
      return request(`/admin/orders${query ? `?${query}` : ''}`);
    },
    updateOrderStatus(id, status) {
      return request(`/admin/orders/${id}/status`, { method: 'PATCH', json: { status } });
    },
    users() {
      return request('/admin/users');
    },
    reviews(limit = 40) {
      return request(`/admin/reviews?limit=${limit}`);
    },
    analytics() {
      return request('/analytics/overview');
    },
    updateRole(id, role) {
      return request(`/admin/users/${id}/role`, { method: 'PATCH', json: { role } });
    },
    createBook(payload) {
      return request('/books', { method: 'POST', json: payload });
    },
    updateBook(id, payload) {
      return request(`/books/${id}`, { method: 'PATCH', json: payload });
    },
    deleteBook(id) {
      return request(`/books/${id}`, { method: 'DELETE' });
    },
  },
};
