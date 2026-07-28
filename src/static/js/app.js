/* ═══════════════════════════════════════════════════════════════
   APP — SPA controller with overlay loading + toasts
   ═══════════════════════════════════════════════════════════════ */

const APP = {
  state: {
    region: 'Todas',
    year: 'Todos',
    segment: 'Todos',
    theme: localStorage.getItem('theme') || 'dark',
    page: 'overview',
    loading: false,
    sidebarCollapsed: localStorage.getItem('sidebar') === 'collapsed',
    totalRecords: 0,
  },

  async init() {
    document.documentElement.setAttribute('data-theme', this.state.theme);
    this._updateThemeUI();

    if (this.state.sidebarCollapsed) {
      document.getElementById('sidebar').classList.add('is-collapsed');
    }

    const filters = await API.filters();
    this._populateSelect('.filter-region', filters.regions, 'Todas');
    this._populateSelect('.filter-year', filters.years, 'Todos');
    this._populateSelect('.filter-segment', filters.segments, 'Todos');
    this.state.totalRecords = filters.total_fact_rows || 0;

    document.getElementById('sidebarToggle').addEventListener('click', () => this.toggleSidebar());
    document.getElementById('themeBtn').addEventListener('click', () => this.toggleTheme());
    document.querySelectorAll('.filter-region').forEach(el => el.addEventListener('change', e => this.setFilter('region', e.target.value)));
    document.querySelectorAll('.filter-year').forEach(el => el.addEventListener('change', e => this.setFilter('year', e.target.value)));
    document.querySelectorAll('.filter-segment').forEach(el => el.addEventListener('change', e => this.setFilter('segment', e.target.value)));

    document.querySelectorAll('.nav-item').forEach(a => {
      a.addEventListener('click', e => {
        e.preventDefault();
        this.navigate(a.dataset.page);
      });
    });

    document.querySelectorAll('.export-btn').forEach(btn => {
      btn.addEventListener('click', e => {
        e.preventDefault();
        this.exportModule(btn.dataset.module);
      });
    });

    const hash = location.hash.slice(1) || 'overview';
    this.navigate(hash);
    window.addEventListener('hashchange', () => {
      const page = location.hash.slice(1) || 'overview';
      this.navigate(page);
    });
  },

  /* ── Loading overlay ────────────────────────────────────── */
  showLoading() {
    document.getElementById('loadingOverlay').classList.add('active');
  },
  hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
  },

  /* ── Toast notifications ────────────────────────────────── */
  toast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = {
      info: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>',
      success: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
      error: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
      warning: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    };
    toast.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span><span class="toast-msg">${message}</span>`;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('toast-show'));
    setTimeout(() => {
      toast.classList.remove('toast-show');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  /* ── Sidebar ────────────────────────────────────────────── */
  toggleSidebar() {
    this.state.sidebarCollapsed = !this.state.sidebarCollapsed;
    document.getElementById('sidebar').classList.toggle('is-collapsed');
    localStorage.setItem('sidebar', this.state.sidebarCollapsed ? 'collapsed' : 'expanded');
    window.dispatchEvent(new Event('resize'));
  },

  _populateSelect(sel, options, selected) {
    document.querySelectorAll(sel).forEach(el => {
      el.innerHTML = options.map(v =>
        `<option value="${v}" ${v === selected ? 'selected' : ''}>${v}</option>`
      ).join('');
    });
  },

  /* ── Filters ────────────────────────────────────────────── */
  setFilter(key, value) {
    this.state[key] = value;
    this._updateActiveFilters();
    this._loadPage(this.state.page);
  },

  _updateActiveFilters() {
    const active = [];
    if (this.state.region !== 'Todas') active.push(this.state.region);
    if (this.state.year !== 'Todos') active.push(this.state.year);
    if (this.state.segment !== 'Todos') active.push(this.state.segment);
    document.getElementById('filterBadge').textContent = active.length ? active.join(' · ') : 'Sin filtros';
  },

  _updateSidebarCount(total, filtered) {
    const el = document.getElementById('sidebarCount');
    const bar = document.getElementById('sidebarBar');
    if (el) el.textContent = `${filtered.toLocaleString()} / ${total.toLocaleString()}`;
    if (bar) bar.style.width = total ? `${(filtered / total * 100).toFixed(1)}%` : '0%';
  },

  _updateSidebarTotal(total) {
    this.state.totalRecords = total;
  },

  /* ── Theme ──────────────────────────────────────────────── */
  _updateThemeUI() {
    const isDark = this.state.theme === 'dark';
    document.getElementById('themeBtn').querySelector('.theme-label').textContent =
      isDark ? 'Tema claro' : 'Tema oscuro';
  },

  toggleTheme() {
    this.state.theme = this.state.theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', this.state.theme);
    this._updateThemeUI();
    localStorage.setItem('theme', this.state.theme);
    this._loadPage(this.state.page);
  },

  /* ── Module Export (Excel) ─────────────────────────────── */
  exportModule(module) {
    this.toast('Generando Excel...', 'info', 2000);
    const q = `region=${encodeURIComponent(this.state.region)}&year=${encodeURIComponent(this.state.year)}&segment=${encodeURIComponent(this.state.segment)}`;
    const url = `/api/export/${module}?${q}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = `superstore_${module}_${this.state.region}_${this.state.year}.xlsx`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  },

  /* ── Navigation ─────────────────────────────────────────── */
  navigate(page) {
    const titles = {
      overview: 'Resumen Ejecutivo',
      sales: 'Analisis de Ventas',
      profitability: 'Analisis de Rentabilidad',
      customers: 'Analisis de Clientes',
      shipping: 'Analisis de Envios',
    };

    this.state.page = page;
    document.getElementById('pageTitle').textContent = titles[page] || page;

    document.querySelectorAll('.nav-item').forEach(a => {
      a.classList.toggle('active', a.dataset.page === page);
    });

    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const target = document.getElementById(`page-${page}`);
    if (target) {
      target.classList.add('active');
      target.style.animation = 'none';
      requestAnimationFrame(() => { target.style.animation = ''; });
    }

    if (location.hash !== `#${page}`) {
      history.pushState(null, '', `#${page}`);
    }

    this._loadPage(page);
    document.getElementById('mainContent').scrollTop = 0;
  },

  /* ── Page Loader ────────────────────────────────────────── */
  async _loadPage(page) {
    if (this.state.loading) return;
    this.state.loading = true;
    this.showLoading();

    const subtitle = `${this.state.region === 'Todas' ? 'Todas las regiones' : this.state.region} · ${this.state.year === 'Todos' ? 'Todos los anos' : this.state.year}`;

    try {
      const theme = this.state.theme;

      switch (page) {
        case 'overview': {
          const d = await API.overview(this.state.region, this.state.year, this.state.segment, theme);
          document.getElementById('ovSubtitle').textContent = subtitle;
          this._updateSidebarTotal(d.kpis.total_fact_rows);
          this._updateSidebarCount(d.kpis.total_fact_rows, d.kpis.total_orders);
          R.kpis(document.getElementById('kpiRow'), d.kpis);
          R.plot(document.getElementById('chartRegionDonut'), d.chart_region_donut);
          R.plot(document.getElementById('chartCategoryBar'), d.chart_category);
          R.top5Mini(document.getElementById('top5ProductsList'), d.top5_products);
          R.plot(document.getElementById('chartTrend'), d.chart_monthly_trend);
          R.paretoCard(document.getElementById('paretoCard'), d.pareto);
          R.momCard(document.getElementById('momCard'), d.mom);
          R.alerts(document.getElementById('alertRow'), d.alerts);
          break;
        }
        case 'sales': {
          const d = await API.sales(this.state.region, this.state.year, this.state.segment, theme);
          document.getElementById('salesSubtitle').textContent = subtitle;
          this._updateSidebarCount(this.state.totalRecords || 0, d.filtered_orders || 0);
          R.plot(document.getElementById('chartSalesCat'), d.chart_category);
          R.plot(document.getElementById('chartSalesReg'), d.chart_region);
          R.plot(document.getElementById('chartSalesMonthly'), d.chart_monthly);
          R.topProducts(document.getElementById('topProductsTable'), d.top_products);
          R.plot(document.getElementById('chartSalesSubcat'), d.chart_subcategory);
          R.plot(document.getElementById('chartSalesMap'), d.chart_map);
          R.plot(document.getElementById('chartSalesCity'), d.chart_city);
          break;
        }
        case 'profitability': {
          const d = await API.profitability(this.state.region, this.state.year, this.state.segment, theme);
          document.getElementById('profSubtitle').textContent = subtitle;
          this._updateSidebarCount(this.state.totalRecords || 0, d.filtered_orders || 0);
          R.discountCallout(document.getElementById('discountCallout'), d.discount_loss_fmt, d.discount_pct);
          R.plot(document.getElementById('chartProfitDiscount'), d.chart_discount);
          R.tiers(document.getElementById('tierCards'), d.tiers);
          R.plot(document.getElementById('chartProfitRegCat'), d.chart_region_category);
          break;
        }
        case 'customers': {
          const d = await API.customers(this.state.region, this.state.year, this.state.segment, theme);
          document.getElementById('custSubtitle').textContent = subtitle;
          this._updateSidebarCount(this.state.totalRecords || 0, d.filtered_orders || 0);
          R.segments(document.getElementById('segmentCards'), d.segments);
          R.plot(document.getElementById('chartSegment'), d.chart_segment);
          R.plot(document.getElementById('chartSegmentMargin'), d.chart_segment_margin);
          R.plot(document.getElementById('chartFrequency'), d.chart_frequency);
          R.topCustomers(document.getElementById('topCustomersTable'), d.top_customers);
          R.insight(document.getElementById('customerInsight'), d.insight);
          break;
        }
        case 'shipping': {
          const d = await API.shipping(this.state.region, this.state.year, this.state.segment, theme);
          document.getElementById('shipSubtitle').textContent = subtitle;
          this._updateSidebarCount(this.state.totalRecords || 0, d.filtered_orders || 0);
          R.shipStats(document.getElementById('shipStatsRow'), d.stats);
          R.shipRegionKpis(document.getElementById('shipRegionKpis'), d.region_kpis);
          R.plot(document.getElementById('chartShipByRegion'), d.chart_by_region);
          R.plot(document.getElementById('chartShipModeImpact'), d.chart_mode_impact);
          R.plot(document.getElementById('chartShipHistogram'), d.chart_histogram);
          break;
        }
      }
    } catch (err) {
      console.error('Error loading page:', err);
      this.toast('Error cargando datos. Verifica la conexion a la base de datos.', 'error', 6000);
    } finally {
      this.state.loading = false;
      this.hideLoading();
    }
  },
};

document.addEventListener('DOMContentLoaded', () => APP.init());