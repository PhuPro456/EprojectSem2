import { api } from '../api.js';
import { ICONS, categoryName, emptyView, esc, money } from '../ui.js';

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

function kpi(icon, label, value, hint) {
  return `<article class="kpi">
    <span class="kpi-icon">${icon}</span>
    <div><span class="kpi-label">${esc(label)}</span><strong>${esc(value)}</strong><span class="kpi-hint">${esc(hint)}</span></div>
  </article>`;
}

function shortMoney(value) {
  const number = Number(value) || 0;
  if (number >= 1000) return `$${(number / 1000).toFixed(1)}k`;
  return `$${Math.round(number)}`;
}

function revenueChart(points) {
  const width = 760;
  const height = 260;
  const left = 48;
  const right = 18;
  const top = 18;
  const bottom = 34;
  const innerW = width - left - right;
  const innerH = height - top - bottom;
  const max = Math.max(...points.map((point) => point.revenue), 1);
  const step = points.length > 1 ? innerW / (points.length - 1) : innerW;
  const x = (index) => left + index * step;
  const y = (value) => top + innerH - (value / max) * innerH;
  const coords = points.map((point, index) => [x(index), y(point.revenue)]);
  const line = coords
    .map(([cx, cy], index) => `${index ? 'L' : 'M'}${cx.toFixed(1)} ${cy.toFixed(1)}`)
    .join(' ');
  const area = `${line} L${x(points.length - 1).toFixed(1)} ${top + innerH} L${left} ${top + innerH} Z`;

  const grid = [0, 0.25, 0.5, 0.75, 1]
    .map((ratio) => {
      const gy = (top + innerH - ratio * innerH).toFixed(1);
      return `<line x1="${left}" y1="${gy}" x2="${width - right}" y2="${gy}" class="chart-grid"/>
        <text x="${left - 8}" y="${Number(gy) + 4}" text-anchor="end" class="chart-axis">${shortMoney(max * ratio)}</text>`;
    })
    .join('');

  const dots = coords
    .map(
      ([cx, cy], index) =>
        `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="4" class="chart-dot"><title>${points[index].label}: ${money(points[index].revenue)} · ${points[index].orders} orders</title></circle>`,
    )
    .join('');

  const labels = points
    .map(
      (point, index) =>
        `<text x="${x(index).toFixed(1)}" y="${height - 10}" text-anchor="middle" class="chart-axis">${esc(point.label)}</text>`,
    )
    .join('');

  return `<svg class="chart-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Revenue by month">
    <defs><linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="rgba(31,77,59,0.28)"/>
      <stop offset="100%" stop-color="rgba(31,77,59,0.02)"/>
    </linearGradient></defs>
    ${grid}
    <path d="${area}" fill="url(#revenueFill)"/>
    <path d="${line}" class="chart-line"/>
    ${dots}
    ${labels}
  </svg>`;
}

function categoryBars(points) {
  if (!points.length) return emptyView('No sales yet', 'Category revenue appears after the first order.');
  const max = Math.max(...points.map((point) => point.revenue), 1);
  return `<ul class="bar-list">${points
    .map(
      (point) => `<li class="bar-row">
        <div class="bar-label"><span>${esc(categoryName(point.category))}</span><strong>${money(point.revenue)}</strong></div>
        <div class="bar-track"><span class="bar-fill" style="width:${((point.revenue / max) * 100).toFixed(1)}%"></span></div>
        <span class="bar-note">${point.units} units sold</span>
      </li>`,
    )
    .join('')}</ul>`;
}

function statusMix(points) {
  const total = points.reduce((sum, point) => sum + point.count, 0);
  if (!total) return emptyView('No orders yet', 'Status distribution appears after checkout.');
  const segments = points
    .filter((point) => point.count > 0)
    .map(
      (point) => `<span class="mix-seg seg-${esc(point.status)}" style="width:${((point.count / total) * 100).toFixed(1)}%" title="${esc(point.status)}: ${point.count}"></span>`,
    )
    .join('');
  const legend = points
    .map(
      (point) => `<li><span class="legend-dot seg-${esc(point.status)}"></span><span>${esc(point.status)}</span><strong>${point.count}</strong></li>`,
    )
    .join('');
  return `<div class="mix-bar">${segments}</div><ul class="mix-legend">${legend}</ul>`;
}

function newCustomerChart(points) {
  const max = Math.max(...points.map((point) => point.new_customers), 1);
  return `<div class="mini-chart">${points
    .map((point) => {
      const height = point.new_customers ? Math.max(8, (point.new_customers / max) * 100) : 2;
      return `<div class="mini-col" title="${esc(point.label)}: ${point.new_customers} new customers">
        <span class="mini-bar" style="height:${height.toFixed(1)}%"><em>${point.new_customers}</em></span>
        <small>${esc(point.label)}</small>
      </div>`;
    })
    .join('')}</div>`;
}

export async function renderAdminAnalytics(main) {
  main.innerHTML = `<div class="admin-page analytics-page">
    <div class="analytics-banner">
      <div><p class="eyebrow">Business intelligence</p><h2>Sales &amp; customer overview</h2><p class="muted">Live from non-cancelled orders, inventory and reader accounts.</p></div>
      <span class="live-chip"><i></i>Live data</span>
    </div>
    <div class="kpi-grid" id="analyticsKpis">${'<div class="kpi skeleton" style="height:104px"></div>'.repeat(5)}</div>
    <div class="analytics-grid" id="analyticsGrid" hidden></div>
  </div>`;

  try {
    const data = await api.admin.analytics();
    const growth = Number(data.growth_rate) || 0;
    main.querySelector('#analyticsKpis').innerHTML = [
      kpi(ICONS.chart, 'Total revenue', money(data.total_revenue), `${data.total_orders} orders counted`),
      kpi(ICONS.receipt, 'Orders', String(data.total_orders), `${data.units_sold} units sold`),
      kpi(ICONS.box, 'Average order', money(data.average_order_value), 'per non-cancelled order'),
      kpi(ICONS.users, 'Customers', String(data.total_customers), `${data.repeat_customers} repeat readers`),
      kpi(
        ICONS.spark,
        'Monthly growth',
        `${growth >= 0 ? '+' : ''}${growth.toFixed(1)}%`,
        `${data.low_stock_books} low-stock titles`,
      ),
    ].join('');

    const grid = main.querySelector('#analyticsGrid');
    grid.hidden = false;
    grid.innerHTML = `
      <section class="panel wide">
        <header class="panel-head"><h2>Revenue by month</h2><span class="muted">Last 8 months</span></header>
        ${revenueChart(data.sales_by_month)}
      </section>
      <section class="panel">
        <header class="panel-head"><h2>Order status mix</h2><span class="muted">All orders</span></header>
        ${statusMix(data.order_statuses)}
      </section>
      <section class="panel">
        <header class="panel-head"><h2>Revenue by category</h2><span class="muted">Non-cancelled</span></header>
        ${categoryBars(data.sales_by_category)}
      </section>
      <section class="panel">
        <header class="panel-head"><h2>New customers</h2><span class="muted">Monthly sign-ups</span></header>
        ${newCustomerChart(data.new_customers_by_month)}
      </section>
      <section class="panel">
        <header class="panel-head"><h2>Top products</h2><span class="muted">By revenue</span></header>
        ${
          data.top_products.length
            ? `<div class="table-wrap"><table class="data-table compact">
                <thead><tr><th>Title</th><th>Units</th><th>Revenue</th></tr></thead>
                <tbody>${data.top_products
                  .map(
                    (product) => `<tr>
                      <td><a href="#/book/${product.book_id}">${esc(product.title)}</a></td>
                      <td>${product.units}</td>
                      <td>${money(product.revenue)}</td>
                    </tr>`,
                  )
                  .join('')}</tbody>
              </table></div>`
            : emptyView('No product sales yet', 'Top titles appear once orders are placed.')
        }
      </section>
      <section class="panel wide">
        <header class="panel-head"><h2>Top customers</h2><span class="muted">By lifetime spend</span></header>
        ${
          data.top_customers.length
            ? `<div class="table-wrap"><table class="data-table compact">
                <thead><tr><th>Customer</th><th>Orders</th><th>Spend</th></tr></thead>
                <tbody>${data.top_customers
                  .map(
                    (customer) => `<tr>
                      <td><div><strong>${esc(customer.name)}</strong><span class="muted block">${esc(customer.email)}</span></div></td>
                      <td>${customer.orders}</td>
                      <td>${money(customer.spend)}</td>
                    </tr>`,
                  )
                  .join('')}</tbody>
              </table></div>`
            : emptyView('No customers yet', 'Registered readers will appear here.')
        }
      </section>`;
  } catch (error) {
    main.querySelector('#analyticsKpis').innerHTML = '';
    const grid = main.querySelector('#analyticsGrid');
    grid.hidden = false;
    grid.innerHTML = `<div class="state-card"><h3>Could not load analytics</h3><p>${esc(error.message)}</p><button class="btn" type="button" data-retry>Try again</button></div>`;
    grid.querySelector('[data-retry]')?.addEventListener('click', () => renderAdminAnalytics(main));
  }
}

function stars(rating) {
  const filled = Math.max(0, Math.min(5, Number(rating) || 0));
  return `<span class="stars" aria-label="${filled} out of 5">${'★'.repeat(filled)}${'☆'.repeat(5 - filled)}</span>`;
}

function keywordCloud(keywords, kind) {
  if (!keywords.length) {
    return `<p class="muted">No ${kind} themes detected in the current reviews.</p>`;
  }
  return `<div class="keyword-cloud">${keywords
    .map(
      (keyword) => `<span class="keyword-chip ${kind}">${esc(keyword.keyword)}<em>${keyword.count}</em></span>`,
    )
    .join('')}</div>`;
}

export async function renderAdminReviews(main) {
  main.innerHTML = `<div class="admin-page">
    <div class="analytics-banner">
      <div><p class="eyebrow">Voice of the reader</p><h2>Review sentiment</h2><p class="muted">Every review is classified locally into positive, neutral or negative with keyword extraction.</p></div>
      <span class="live-chip"><i></i>Lexicon model</span>
    </div>
    <div class="kpi-grid" id="reviewKpis">${'<div class="kpi skeleton" style="height:104px"></div>'.repeat(4)}</div>
    <div class="analytics-grid" id="reviewGrid" hidden></div>
  </div>`;

  try {
    const data = await api.admin.reviews(60);
    const { summary } = data;
    const positiveShare = summary.total ? Math.round((summary.positive / summary.total) * 100) : 0;

    main.querySelector('#reviewKpis').innerHTML = [
      kpi(ICONS.spark, 'Reviews', String(summary.total), 'across the catalog'),
      kpi(ICONS.chart, 'Average rating', `${summary.average_rating.toFixed(2)} / 5`, `${'★'.repeat(Math.round(summary.average_rating)) || 'No ratings'}`),
      kpi(ICONS.book, 'Positive share', `${positiveShare}%`, `${summary.positive} positive reviews`),
      kpi(ICONS.close, 'Negative reviews', String(summary.negative), `${summary.neutral} neutral`),
    ].join('');

    const grid = main.querySelector('#reviewGrid');
    grid.hidden = false;
    grid.innerHTML = `
      <section class="panel">
        <header class="panel-head"><h2>Positive themes</h2><span class="muted">Most mentioned</span></header>
        ${keywordCloud(data.positive_keywords, 'positive')}
      </section>
      <section class="panel">
        <header class="panel-head"><h2>Negative themes</h2><span class="muted">Most mentioned</span></header>
        ${keywordCloud(data.negative_keywords, 'negative')}
      </section>
      <section class="panel wide">
        <header class="panel-head"><h2>Latest reviews</h2><span class="muted">${data.items.length} shown</span></header>
        ${
          data.items.length
            ? `<div class="table-wrap"><table class="data-table">
                <thead><tr><th>Book</th><th>Reader</th><th>Rating</th><th>Sentiment</th><th>Review</th><th>Date</th></tr></thead>
                <tbody>${data.items
                  .map(
                    (review) => `<tr>
                      <td><a href="#/book/${review.book_id}">${esc(review.book_title)}</a></td>
                      <td>${esc(review.author_name)}</td>
                      <td>${stars(review.rating)}</td>
                      <td><span class="sentiment-pill ${esc(review.sentiment)}">${esc(review.sentiment)}</span></td>
                      <td class="review-quote">${esc(review.text)}</td>
                      <td class="muted">${esc(formatDate(review.created_at))}</td>
                    </tr>`,
                  )
                  .join('')}</tbody>
              </table></div>`
            : emptyView('No reviews yet', 'Reader reviews will appear here once they are submitted.')
        }
      </section>`;
  } catch (error) {
    main.querySelector('#reviewKpis').innerHTML = '';
    const grid = main.querySelector('#reviewGrid');
    grid.hidden = false;
    grid.innerHTML = `<div class="state-card"><h3>Could not load reviews</h3><p>${esc(error.message)}</p><button class="btn" type="button" data-retry>Try again</button></div>`;
    grid.querySelector('[data-retry]')?.addEventListener('click', () => renderAdminReviews(main));
  }
}
