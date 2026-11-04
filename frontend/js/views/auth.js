import { api } from '../api.js';
import { loadUser, setToken } from '../store.js';
import { toast } from '../ui.js';

const DEMO_ACCOUNTS = [
  {
    label: 'Admin console',
    email: 'admin@bookstorepro.com',
    password: 'admin-password-123',
    next: '#/admin',
  },
  {
    label: 'Shopper',
    email: 'maya.chen@example.com',
    password: 'reader-password-1',
    next: '#/',
  },
];

function afterAuth() {
  const next = sessionStorage.getItem('bookstore.next') || '#/';
  sessionStorage.removeItem('bookstore.next');
  const reopenCart = sessionStorage.getItem('bookstore.reopenCart') === '1';
  sessionStorage.removeItem('bookstore.reopenCart');
  location.hash = next;
  if (reopenCart) {
    setTimeout(() => document.dispatchEvent(new Event('open-cart')), 80);
  }
}

function showError(errorNode, message) {
  errorNode.textContent = message;
  errorNode.hidden = false;
}

function setPending(button, pending, label) {
  button.disabled = pending;
  button.textContent = pending ? 'Please wait…' : label;
}

export async function renderLogin(main) {
  main.innerHTML = `
    <div class="auth-page">
      <div class="auth-card">
        <p class="eyebrow">Welcome back</p>
        <h1>Sign in</h1>
        <p class="auth-sub">Track your orders, check out faster, and keep your cart between visits.</p>
        <form class="form" id="loginForm" novalidate>
          <label>Email<input type="email" name="email" required autocomplete="email" placeholder="you@example.com"></label>
          <label>Password<input type="password" name="password" required autocomplete="current-password" placeholder="Your password"></label>
          <p class="form-error" id="formError" hidden></p>
          <button class="btn full" type="submit">Sign in</button>
        </form>
        <div class="auth-demo">
          <p class="auth-demo-title">Demo accounts</p>
          <div class="auth-demo-actions">
            ${DEMO_ACCOUNTS.map(
              (account) => `
              <button class="auth-demo-btn" type="button" data-demo-email="${account.email}">
                <span class="auth-demo-role">${account.label}</span>
                <span class="auth-demo-mail">${account.email}</span>
              </button>`
            ).join('')}
          </div>
          <p class="auth-demo-hint">Pick one to fill the form and sign straight in.</p>
        </div>
        <p class="auth-alt">New here? <a href="#/register">Create an account</a></p>
      </div>
    </div>`;

  const form = main.querySelector('#loginForm');
  const errorNode = main.querySelector('#formError');

  const submitLogin = async () => {
    errorNode.hidden = true;
    const button = form.querySelector('button[type="submit"]');
    const email = form.email.value.trim();
    const password = form.password.value;
    if (!email || !password) {
      showError(errorNode, 'Enter your email and password.');
      return;
    }
    setPending(button, true, 'Sign in');
    try {
      const token = await api.login(email, password);
      setToken(token.access_token);
      await loadUser();
      toast('Signed in', 'success');
      afterAuth();
    } catch (error) {
      showError(errorNode, error.message);
    } finally {
      setPending(button, false, 'Sign in');
    }
  };

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    submitLogin();
  });

  main.querySelectorAll('.auth-demo-btn').forEach((button) => {
    button.addEventListener('click', () => {
      const account = DEMO_ACCOUNTS.find(
        (item) => item.email === button.dataset.demoEmail
      );
      form.email.value = account.email;
      form.password.value = account.password;
      sessionStorage.setItem('bookstore.next', account.next);
      submitLogin();
    });
  });
}

export async function renderRegister(main) {
  main.innerHTML = `
    <div class="auth-page">
      <div class="auth-card">
        <p class="eyebrow">Join the club</p>
        <h1>Create account</h1>
        <p class="auth-sub">One account for orders, faster checkout, and your reading history.</p>
        <form class="form" id="registerForm" novalidate>
          <label>Name<input type="text" name="name" required maxlength="100" autocomplete="name" placeholder="Ada Lovelace"></label>
          <label>Email<input type="email" name="email" required autocomplete="email" placeholder="you@example.com"></label>
          <label>Password<input type="password" name="password" required minlength="8" maxlength="128" autocomplete="new-password" placeholder="At least 8 characters"></label>
          <p class="form-error" id="formError" hidden></p>
          <button class="btn full" type="submit">Create account</button>
        </form>
        <p class="auth-alt">Already have an account? <a href="#/login">Sign in</a></p>
      </div>
    </div>`;

  const form = main.querySelector('#registerForm');
  const errorNode = main.querySelector('#formError');

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorNode.hidden = true;
    const name = form.name.value.trim();
    const email = form.email.value.trim();
    const password = form.password.value;
    if (name.length < 1 || !email || password.length < 8) {
      showError(errorNode, 'Name, a valid email, and a password of at least 8 characters are required.');
      return;
    }
    const button = form.querySelector('button[type="submit"]');
    setPending(button, true, 'Create account');
    try {
      await api.register({ name, email, password });
      const token = await api.login(email, password);
      setToken(token.access_token);
      await loadUser();
      toast('Account created — welcome aboard', 'success');
      afterAuth();
    } catch (error) {
      showError(errorNode, error.message);
    } finally {
      setPending(button, false, 'Create account');
    }
  });
}
