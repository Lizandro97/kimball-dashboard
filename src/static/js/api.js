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

  clearCache() { this._cache.filters = null; }
};
