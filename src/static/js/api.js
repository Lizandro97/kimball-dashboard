/* ── API client ────────────────────────────────────────────────── */
const API = {
  _cache: { filters: null },

  async _fetch(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status} — ${res.statusText}`);
    return res.json();
  },

  filters() {
    if (this._cache.filters) return Promise.resolve(this._cache.filters);
    return this._fetch('/api/filters').then(d => {
      this._cache.filters = d;
      return d;
    });
  },

  overview(region, year, segment, theme) {
    return this._fetch(`/api/overview?region=${encodeURIComponent(region)}&year=${encodeURIComponent(year)}&segment=${encodeURIComponent(segment)}&theme=${theme}`);
  },

  sales(region, year, segment, theme) {
    return this._fetch(`/api/sales?region=${encodeURIComponent(region)}&year=${encodeURIComponent(year)}&segment=${encodeURIComponent(segment)}&theme=${theme}`);
  },

  profitability(region, year, segment, theme) {
    return this._fetch(`/api/profitability?region=${encodeURIComponent(region)}&year=${encodeURIComponent(year)}&segment=${encodeURIComponent(segment)}&theme=${theme}`);
  },

  customers(region, year, segment, theme) {
    return this._fetch(`/api/customers?region=${encodeURIComponent(region)}&year=${encodeURIComponent(year)}&segment=${encodeURIComponent(segment)}&theme=${theme}`);
  },

  shipping(region, year, segment, theme) {
    return this._fetch(`/api/shipping?region=${encodeURIComponent(region)}&year=${encodeURIComponent(year)}&segment=${encodeURIComponent(segment)}&theme=${theme}`);
  },

  /* ── ML ──────────────────────────────────────────────────── */
  rfm() { return this._fetch('/api/ml/rfm'); },
  mlProducts() { return this._fetch('/api/ml/products'); },
  profitSegments() { return this._fetch('/api/ml/profit-segments'); },
  basket(minSupport, minLift) {
    return this._fetch(`/api/ml/basket?min_support=${minSupport || 0.008}&min_lift=${minLift || 1.0}`);
  },
  forecast(months) {
    return this._fetch(`/api/ml/forecast?months_ahead=${months || 6}`);
  },
  profitPredict(sales, discount, qty, category, region, segment, ship, month) {
    return this._fetch(`/api/ml/profit-predict?sales=${sales}&discount=${discount}&quantity=${qty}&category=${encodeURIComponent(category)}&region=${encodeURIComponent(region)}&segment=${encodeURIComponent(segment)}&ship_mode=${encodeURIComponent(ship)}&month=${month || 7}`);
  },
  profitPredictInfo() { return this._fetch('/api/ml/profit-predict/info'); },

  clearCache() { this._cache.filters = null; }
};
