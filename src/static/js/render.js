/* ═══════════════════════════════════════════════════════════════
   RENDER — Premium component renderers
   ═══════════════════════════════════════════════════════════════ */

const R = {

  /* ── Chart renderer ───────────────────────────────────────── */
  plot(el, fig) {
    if (!fig || !fig.data) return;
    const theme = document.documentElement.getAttribute('data-theme');
    const isDark = theme === 'dark';
    const layout = Object.assign({}, fig.layout || {});
    layout.paper_bgcolor = 'rgba(0,0,0,0)';
    layout.plot_bgcolor = 'rgba(0,0,0,0)';
    layout.font = Object.assign({ color: isDark ? '#94A3B8' : '#475569', family: 'Inter, sans-serif', size: 12 }, layout.font || {});
    layout.margin = Object.assign({ l: 60, r: 24, t: 60, b: 60 }, layout.margin || {});
    if (layout.xaxis) {
      layout.xaxis.gridcolor = isDark ? 'rgba(148,163,184,0.08)' : 'rgba(0,0,0,0.04)';
      layout.xaxis.zerolinecolor = isDark ? 'rgba(148,163,184,0.08)' : 'rgba(0,0,0,0.04)';
      layout.xaxis.automargin = true;
    }
    if (layout.yaxis) {
      layout.yaxis.gridcolor = isDark ? 'rgba(148,163,184,0.08)' : 'rgba(0,0,0,0.04)';
      layout.yaxis.zerolinecolor = isDark ? 'rgba(148,163,184,0.08)' : 'rgba(0,0,0,0.04)';
      layout.yaxis.automargin = true;
    }
    layout.autosize = true;
    layout.hoverlabel = Object.assign({
      bgcolor: isDark ? '#1F2937' : '#FFFFFF',
      bordercolor: isDark ? '#334155' : '#E2E8F0',
      font: { color: isDark ? '#F1F5F9' : '#0F172A', family: 'Inter' },
    }, layout.hoverlabel || {});
    if (layout.legend) {
      layout.legend.bgcolor = 'rgba(0,0,0,0)';
      layout.legend.font = Object.assign({ color: isDark ? '#94A3B8' : '#475569' }, layout.legend.font || {});
    }
    Plotly.react(el, fig.data, layout, { responsive: true, displayModeBar: false, scrollZoom: false });
  },

  /* ── KPI Cards ────────────────────────────────────────────── */
  kpis(container, kpis) {
    const accents = ['var(--neon-blue)', 'var(--neon-green)', 'var(--neon-cyan)', 'var(--neon-amber)', 'var(--neon-purple)'];
    const items = [
      { label: 'Ingresos', value: kpis.total_sales_fmt, delta: kpis.yoy_sales },
      { label: 'Utilidad', value: kpis.total_profit_fmt, delta: kpis.yoy_profit },
      { label: 'Ordenes', value: kpis.total_orders.toLocaleString(), delta: kpis.yoy_orders },
      { label: 'Unidades', value: kpis.total_units.toLocaleString(), delta: null },
      { label: 'Margen', value: kpis.margin + '%', delta: kpis.yoy_margin, unit: 'pp' },
    ];
    container.innerHTML = items.map((c, i) => {
      let cls = 'neutral', sign = '', arrow = '';
      if (c.delta !== null && c.delta !== undefined) {
        cls = c.delta >= 0 ? 'pos' : 'neg';
        sign = c.delta >= 0 ? '+' : '';
        arrow = cls === 'pos' ? '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m18 15-6-6-6 6"/></svg>' : '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>';
      }
      const deltaText = c.delta !== null ? `${arrow} ${sign}${c.delta}${c.unit || '%'}` : '<span style="color:var(--text-faint)">—</span>';
      return `<div class="kpi-card animate-in" style="--kpi-accent:${accents[i]}">
        <div class="kpi-label">${c.label}</div>
        <div class="kpi-value">${c.value}</div>
        <div class="kpi-delta ${cls}">${deltaText}</div>
      </div>`;
    }).join('');
  },

  /* ── Alert Cards ──────────────────────────────────────────── */
  alerts(container, alerts) {
    const isDiscountLoss = alerts.discount_loss < 0;
    const items = [
      {
        icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        cls: isDiscountLoss ? 'red' : 'green',
        accent: isDiscountLoss ? 'var(--neon-red)' : 'var(--neon-green)',
        title: 'Descuentos Agresivos',
        desc: `Transacciones con descuento &gt;50% generan <b>${alerts.discount_loss_fmt}</b> en utilidad.`,
      },
      {
        icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>',
        cls: alerts.south_margin < 8 ? 'amber' : 'green',
        accent: alerts.south_margin < 8 ? 'var(--neon-amber)' : 'var(--neon-green)',
        title: 'Region South',
        desc: `Margen mas bajo del negocio: <b>${alerts.south_margin}%</b>. ${alerts.south_margin < 8 ? 'Requiere revision.' : 'Saludable.'}`,
      },
      {
        icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
        cls: 'blue',
        accent: 'var(--neon-blue)',
        title: 'Categoria Estrella',
        desc: `Technology lidera con margen de <b>${alerts.tech_margin}%</b>.`,
      },
    ];
    container.innerHTML = items.map(a =>
      `<div class="alert-card animate-in" style="--alert-accent:${a.accent}">
        <div class="icon ${a.cls}">${a.icon}</div>
        <div class="title">${a.title}</div>
        <div class="desc">${a.desc}</div>
      </div>`
    ).join('');
  },

  /* ── Top Products Table ───────────────────────────────────── */
  topProducts(container, products) {
    if (!products || !products.length) {
      container.innerHTML = '<div style="padding:var(--space-6);text-align:center;color:var(--text-muted)">Sin datos de productos</div>';
      return;
    }
    let html = `<table><thead><tr>
      <th>#</th><th>Producto</th><th>Categoria</th><th>Subcategoria</th>
      <th class="num">Ventas</th><th class="num">Utilidad</th><th class="num">Margen</th>
    </tr></thead><tbody>`;
    products.forEach((p, i) => {
      let cls = 'green';
      if (p.margen <= 0) cls = 'red';
      else if (p.margen < 20) cls = 'amber';
      html += `<tr>
        <td style="font-family:var(--font-mono);font-size:var(--text-xs);color:var(--text-muted)">${String(i + 1).padStart(2, '0')}</td>
        <td style="font-weight:500;color:var(--text-primary);max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${p.producto}</td>
        <td>${p.categoria}</td>
        <td>${p.subcategoria}</td>
        <td class="num" style="font-weight:600;color:var(--text-primary)">${p.ventas_fmt}</td>
        <td class="num" style="font-weight:600;color:var(--text-primary)">${p.utilidad_fmt}</td>
        <td class="num ${cls}">${p.margen}%</td>
      </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
  },

  /* ── Discount Tiers ───────────────────────────────────────── */
  tiers(container, tiers) {
    container.innerHTML = tiers.map(t => {
      const sign = t.utilidad >= 0 ? '+' : '';
      const cls = t.utilidad >= 0 ? 'pos' : 'neg';
      return `<div class="tier-card">
        <span class="tier-name">${t.nivel}</span>
        <span class="tier-profit ${cls}">${sign}${t.utilidad_fmt}</span>
      </div>`;
    }).join('');
  },

  /* ── Segment Cards ────────────────────────────────────────── */
  segments(container, segments) {
    const config = {
      Consumer: { color: 'var(--neon-blue)', glow: 'rgba(96,165,250,0.3)' },
      Corporate: { color: 'var(--neon-green)', glow: 'rgba(52,211,153,0.3)' },
      'Home Office': { color: 'var(--neon-purple)', glow: 'rgba(167,139,250,0.3)' },
    };
    container.innerHTML = segments.map((s, i) => {
      const c = config[s.segmento] || { color: 'var(--neon-blue)', glow: 'rgba(96,165,250,0.3)' };
      return `<div class="seg-card animate-in" style="--seg-color:${c.color};--seg-glow:${c.glow};animation-delay:${i * 80}ms">
        <div class="count">${s.clientes.toLocaleString()}</div>
        <div class="label">${s.segmento}</div>
        <div class="detail">${s.ingresos_fmt} · ${s.ordenes.toLocaleString()} ordenes</div>
        <div class="detail" style="margin-top:4px;color:${s.margin >= 12 ? 'var(--neon-green)' : 'var(--neon-amber)'}">
          Margen: ${s.margin}% · Desc: ${s.avg_discount}%
        </div>
      </div>`;
    }).join('');
  },

  /* ── Discount Callout ─────────────────────────────────────── */
  discountCallout(container, loss, pct) {
    const isLoss = loss.startsWith('-');
    container.innerHTML = `
      <div class="callout-icon ${isLoss ? 'warn' : 'ok'}">
        ${isLoss
          ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
          : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
        }
      </div>
      <div class="callout-body">
        <b>Perdida por descuentos agresivos</b>
        <span>Transacciones con descuento &gt;50% representan el <strong>${pct}%</strong> del total
        pero generan <strong>${loss}</strong> neto. ${isLoss ? 'Se recomienda revisar la politica.' : 'Se mantiene estable.'}</span>
      </div>`;
  },

  /* ── Customer Insight ─────────────────────────────────────── */
  insight(container, data) {
    if (!data) {
      container.innerHTML = '<div style="padding:var(--space-6);text-align:center;color:var(--text-muted)">Sin datos de insight</div>';
      return;
    }
    container.innerHTML = `
      <div class="callout-icon info">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
      </div>
      <div class="callout-body">
        <b>Perfil del Cliente</b>
        <span>El segmento <strong style="color:var(--neon-blue)">${data.top_segment}</strong> genera la mayor parte de los
        ingresos (<strong>${data.top_ingresos}</strong>). Ticket promedio: <strong>${data.avg_ticket}</strong> por orden.
        <strong>${data.total_customers}</strong> clientes activos, <strong>${data.repeat_rate}%</strong> con compras recurrentes.</span>
      </div>`;
  },

  /* ── Top Customers Table ───────────────────────────────────── */
  topCustomers(container, customers) {
    if (!customers || !customers.length) {
      container.innerHTML = '<div style="padding:var(--space-6);text-align:center;color:var(--text-muted)">Sin datos de clientes</div>';
      return;
    }
    let html = `<table><thead><tr>
      <th>#</th><th>Cliente</th><th>Segmento</th>
      <th class="num">Ingresos</th><th class="num">Ordenes</th>
      <th class="num">Ticket</th><th class="num">Margen</th>
    </tr></thead><tbody>`;
    customers.forEach(c => {
      let marginCls = 'green';
      if (c.margin <= 0) marginCls = 'red';
      else if (c.margin < 20) marginCls = 'amber';
      html += `<tr>
        <td style="font-family:var(--font-mono);font-size:var(--text-xs);color:var(--text-muted)">${String(c.rank).padStart(2, '0')}</td>
        <td style="font-weight:500;color:var(--text-primary)">${c.name}</td>
        <td>${c.segment}</td>
        <td class="num" style="font-weight:600;color:var(--text-primary)">${c.revenue_fmt}</td>
        <td class="num">${c.orders}</td>
        <td class="num">${c.ticket_fmt}</td>
        <td class="num ${marginCls}">${c.margin}%</td>
      </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
  },

  /* ── Shipping Stats ───────────────────────────────────────── */
  shipStats(container, stats) {
    const accents = ['var(--neon-blue)', 'var(--neon-cyan)', 'var(--neon-green)', 'var(--neon-purple)'];
    const modeCount = stats.by_mode ? Object.keys(stats.by_mode).length : 0;
    const items = [
      { label: 'Ordenes enviadas', value: stats.total_orders.toLocaleString() },
      { label: 'Entrega promedio', value: `${stats.avg_delivery_days} dias` },
      { label: 'A tiempo (≤5d)', value: `${stats.on_time_pct}%` },
      { label: 'Modos de envio', value: String(modeCount) },
    ];
    container.innerHTML = items.map((c, i) =>
      `<div class="kpi-card animate-in" style="--kpi-accent:${accents[i]};animation-delay:${i * 60}ms">
        <div class="kpi-label">${c.label}</div>
        <div class="kpi-value">${c.value}</div>
      </div>`
    ).join('');
  },

  /* ── Shipping Region KPIs ─────────────────────────────────── */
  shipRegionKpis(container, regionKpis) {
    if (!regionKpis || !regionKpis.length) {
      container.innerHTML = '';
      return;
    }
    const regionColors = {
      West: 'var(--neon-blue)', East: 'var(--neon-purple)',
      Central: 'var(--neon-amber)', South: 'var(--neon-red)',
    };
    container.innerHTML = regionKpis.map(r => {
      const color = regionColors[r.region] || 'var(--neon-blue)';
      const onTimeColor = r.on_time_pct >= 70 ? 'var(--neon-green)' : r.on_time_pct >= 50 ? 'var(--neon-amber)' : 'var(--neon-red)';
      return `<div class="region-kpi-item animate-in" style="border-left:3px solid ${color}">
        <div class="region-name">${r.region}</div>
        <div class="region-value">${r.avg_days}d</div>
        <div class="region-detail">${r.orders.toLocaleString()} ordenes · ${r.on_time_pct}% a tiempo</div>
      </div>`;
    }).join('');
  },

  /* ── Top 5 Products Mini List ─────────────────────────────── */
  top5Mini(container, products) {
    if (!products || !products.length) {
      container.innerHTML = '<div style="padding:var(--space-4);text-align:center;color:var(--text-muted)">Sin datos</div>';
      return;
    }
    container.innerHTML = products.map((p, i) => {
      const marginCls = p.margin >= 20 ? 'color:var(--neon-green)' : p.margin > 0 ? 'color:var(--neon-amber)' : 'color:var(--neon-red)';
      return `<div class="top5-item">
        <span class="top5-rank">${i + 1}</span>
        <div class="top5-info">
          <div class="top5-name" title="${p.name}">${p.name}</div>
          <div class="top5-cat">${p.category}</div>
        </div>
        <span class="top5-revenue">${p.revenue_fmt}</span>
        <span class="top5-margin" style="${marginCls}">${p.margin}%</span>
      </div>`;
    }).join('');
  },

  /* ── Pareto 80/20 Card ───────────────────────────────────── */
  paretoCard(container, data) {
    if (!data || !data.total_products) {
      container.innerHTML = '<div style="padding:var(--space-4);text-align:center;color:var(--text-muted)">Sin datos</div>';
      return;
    }
    container.innerHTML = `
      <div class="callout-icon info">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
      </div>
      <div class="callout-body">
        <b>Análisis Pareto (80/20)</b>
        <span>
          El <strong>${data.top20_revenue_share}%</strong> de los ingresos proviene del
          <strong>${data.top20_products_count}</strong> productos mas vendidos (${data.total_products} totales).
          El <strong>${data.pct_products_for_80}%</strong> de los productos genera el
          <strong>${data.pct_revenue_from_top}%</strong> de los ingresos.
        </span>
      </div>`;
  },

  /* ── Month-over-Month Card ───────────────────────────────── */
  momCard(container, data) {
    if (!data || !data.has_data) {
      container.innerHTML = '<div style="padding:var(--space-4);text-align:center;color:var(--text-muted)">Sin datos mensuales</div>';
      return;
    }
    const cls = data.mom_pct >= 0 ? 'pos' : 'neg';
    const arrow = data.mom_pct >= 0
      ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m18 15-6-6-6 6"/></svg>'
      : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>';
    container.innerHTML = `
      <div class="callout-icon ${cls === 'pos' ? 'ok' : 'warn'}">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          ${cls === 'pos'
            ? '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
            : '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'}
        </svg>
      </div>
      <div class="callout-body">
        <b>Comparacion Mensual (MoM)</b>
        <span>
          <strong>${data.current_month}</strong>: ${data.current_fmt}
          vs <strong>${data.prev_month}</strong>: ${data.prev_fmt}
          <span class="kpi-delta ${cls}" style="display:inline-flex;margin-left:8px">${arrow} ${Math.abs(data.mom_pct)}%</span>
        </span>
      </div>`;
  },

  /* ═══════════════════════════════════════════════════════════════
     ML RENDERERS
     ═══════════════════════════════════════════════════════════════ */

  /* ── RFM KPI cards ────────────────────────────────────────── */
  mlRfmKpis(container, segments) {
    const colors = ['var(--neon-blue)', 'var(--neon-green)', 'var(--neon-amber)', 'var(--neon-red)'];
    container.innerHTML = segments.map((s, i) =>
      `<div class="kpi-card animate-in" style="--kpi-accent:${colors[i]}">
        <div class="kpi-label">${s.label}</div>
        <div class="kpi-value">${s.clientes}</div>
        <div class="kpi-delta pos" style="color:var(--text-muted);font-size:var(--text-xs)">R:${s.avg_recency_dias}d · F:${s.avg_frequency.toFixed(1)} · M:$${s.avg_monetary_usd.toFixed(0)}</div>
      </div>`
    ).join('');
  },

  /* ── RFM Scatter 3D ──────────────────────────────────────── */
  mlRfmScatter(el, scatter) {
    if (!scatter || !scatter.length) return;
    const clusters = [...new Set(scatter.map(d => d.cluster))];
    const colors = ['#60A5FA', '#34D399', '#FBBF24', '#F87171', '#A78BFA'];
    const traces = clusters.map(c => {
      const pts = scatter.filter(d => d.cluster === c);
      return {
        x: pts.map(d => d.recency), y: pts.map(d => d.frequency), z: pts.map(d => d.monetary),
        mode: 'markers', type: 'scatter3d',
        name: `Cluster ${c}`,
        marker: { size: 3, color: colors[c] || '#94A3B8', opacity: 0.7 },
      };
    });
    R.plot(el, { data: traces, layout: { scene: { xaxis: { title: 'Recency' }, yaxis: { title: 'Frequency' }, zaxis: { title: 'Monetary' } }, margin: { l: 0, r: 0, t: 24, b: 0 }, height: 480 } });
  },

  /* ── RFM Table ───────────────────────────────────────────── */
  mlRfmTable(container, segments) {
    let html = `<table><thead><tr><th>Cluster</th><th class="num">Clientes</th><th class="num">Recencia</th><th class="num">Frecuencia</th><th class="num">Monetario</th></tr></thead><tbody>`;
    segments.forEach(s => { html += `<tr><td style="font-weight:600;color:var(--text-primary)">${s.label}</td><td class="num">${s.clientes}</td><td class="num">${s.avg_recency_dias}d</td><td class="num">${s.avg_frequency.toFixed(2)}</td><td class="num">$${s.avg_monetary_usd.toFixed(2)}</td></tr>`; });
    html += '</tbody></table>';
    container.innerHTML = html;
  },

  /* ── Product Segments KPIs ────────────────────────────────── */
  mlProdKpis(container, segments) {
    const colors = ['var(--neon-green)', 'var(--neon-blue)', 'var(--neon-amber)', 'var(--neon-red)'];
    container.innerHTML = segments.map((s, i) =>
      `<div class="kpi-card animate-in" style="--kpi-accent:${colors[i]}">
        <div class="kpi-label">${s.label}</div>
        <div class="kpi-value">${s.productos}</div>
        <div class="kpi-delta pos" style="color:var(--text-muted);font-size:var(--text-xs)">V:$${s.avg_sales.toFixed(0)} · M:${s.avg_margin_pct}%</div>
      </div>`
    ).join('');
  },

  /* ── Product Scatter 2D ──────────────────────────────────── */
  mlProdScatter(el, scatter) {
    if (!scatter || !scatter.length) return;
    const clusters = [...new Set(scatter.map(d => d.cluster))];
    const colors = ['#34D399', '#60A5FA', '#FBBF24', '#F87171', '#A78BFA'];
    const traces = clusters.map(c => {
      const pts = scatter.filter(d => d.cluster === c);
      return {
        x: pts.map(d => d.sales), y: pts.map(d => d.margin),
        mode: 'markers', type: 'scatter',
        name: `Cluster ${c}`,
        text: pts.map(d => d.producto || ''), hoverinfo: 'text+x+y',
        marker: { size: 6, color: colors[c] || '#94A3B8', opacity: 0.7 },
      };
    });
    R.plot(el, { data: traces, layout: { xaxis: { title: 'Ventas' }, yaxis: { title: 'Margen' } } });
  },

  /* ── Product Table ───────────────────────────────────────── */
  mlProdTable(container, segments) {
    let html = `<table><thead><tr><th>Cluster</th><th class="num">Productos</th><th class="num">Ventas Prom</th><th class="num">Utilidad Prom</th><th class="num">Margen</th><th class="num">Descuento</th></tr></thead><tbody>`;
    segments.forEach(s => {     html += `<tr><td style="font-weight:600;color:var(--text-primary)">${s.label}</td><td class="num">${s.productos}</td><td class="num">$${s.avg_sales.toFixed(2)}</td><td class="num">$${s.avg_profit.toFixed(2)}</td><td class="num">${s.avg_margin_pct}%</td><td class="num">${s.avg_discount_pct}%</td></tr>`; });
    html += '</tbody></table>';
    container.innerHTML = html;
  },

  /* ── Profit Segments Heatmap ──────────────────────────────── */
  mlProfitHeatmap(el, heatmap) {
    if (!heatmap || !heatmap.length) return;
    const regions = [...new Set(heatmap.map(d => d.region))];
    const categories = [...new Set(heatmap.map(d => d.category))];
    const z = regions.map(r => categories.map(c => {
      const match = heatmap.find(d => d.region === r && d.category === c);
      return match ? match.profit : 0;
    }));
    R.plot(el, {
      data: [{
        z, x: categories, y: regions,
        type: 'heatmap', colorscale: 'RdBu',
        hoverongaps: false,
        text: regions.map(r => categories.map(c => {
          const match = heatmap.find(d => d.region === r && d.category === c);
          return match ? `$${match.profit.toFixed(0)}` : '';
        })),
        hoverinfo: 'x+y+text',
      }],
      layout: { xaxis: { title: 'Categoria' }, yaxis: { title: 'Region' } },
    });
  },

  /* ── Profit Segments Table ────────────────────────────────── */
  mlProfitTable(container, heatmap) {
    let html = `<table><thead><tr><th>Region</th><th>Categoria</th><th class="num">Utilidad</th><th class="num">Descuento Prom</th></tr></thead><tbody>`;
    const sorted = [...heatmap].sort((a, b) => b.profit - a.profit);
    sorted.forEach(s => {
      const cls = s.profit >= 0 ? '' : 'red';
      html += `<tr><td>${s.region}</td><td>${s.category}</td><td class="num ${cls}" style="font-weight:600">${s.profit >= 0 ? '' : '-'}$${Math.abs(s.profit).toFixed(2)}</td><td class="num">${s.discount_avg}%</td></tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
  },

  /* ── Basket Rules Table ───────────────────────────────────── */
  mlBasketTable(container, data) {
    if (!data || !data.rules || !data.rules.length) {
      container.innerHTML = '<div style="padding:var(--space-6);text-align:center;color:var(--text-muted)">Sin reglas de asociacion encontradas</div>';
      return;
    }
    let html = `<table><thead><tr><th>#</th><th>Antecedente</th><th>Consecuente</th><th class="num">Support</th><th class="num">Confianza</th><th class="num">Lift</th></tr></thead><tbody>`;
    data.rules.forEach((r, i) => {
      html += `<tr>
        <td style="font-family:var(--font-mono);font-size:var(--text-xs);color:var(--text-muted)">${String(i + 1).padStart(2, '0')}</td>
        <td style="font-weight:500;color:var(--text-primary)">${r.antecedents}</td>
        <td style="font-weight:500;color:var(--neon-green)">${r.consequents}</td>
        <td class="num">${r.support}%</td>
        <td class="num">${r.confidence}%</td>
        <td class="num" style="font-weight:600;color:${r.lift >= 1.5 ? 'var(--neon-green)' : 'var(--text-primary)'}">${r.lift}</td>
      </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
  },

  /* ── Forecast KPI cards ──────────────────────────────────── */
  mlFcstKpis(container, metrics) {
    const sm = metrics.sales || metrics;
    const pm = metrics.profit || {};
    container.innerHTML = [
      { label: 'R² Ventas', value: (sm.r2 || 0).toFixed(3), accent: 'var(--neon-blue)' },
      { label: 'MAPE', value: sm.mape_pct || `${(sm.mape || 0).toFixed(1)}%`, accent: 'var(--neon-amber)' },
      { label: 'Error Prom', value: `$${(sm.mae || 0).toFixed(0)}`, accent: 'var(--neon-cyan)' },
      { label: 'R² Utilidad', value: (pm.r2 || 0).toFixed(3), accent: 'var(--neon-green)' },
    ].map((m, i) =>
      `<div class="kpi-card animate-in" style="--kpi-accent:${m.accent};animation-delay:${i * 80}ms">
        <div class="kpi-label">${m.label}</div>
        <div class="kpi-value">${m.value}</div>
      </div>`
    ).join('');
  },

  /* ── Forecast Chart (dual axis) ──────────────────────────── */
  mlForecast(el, data) {
    if (!data) return;
    const hist = data.historical || [];
    const fc = data.forecast || [];
    const xKey = hist.length && hist[0].date_label ? 'date_label' : 'period';
    const traces = [];
    if (hist.length) {
      traces.push({
        x: hist.map(d => d[xKey]), y: hist.map(d => d.sales),
        type: 'scatter', mode: 'lines+markers',
        name: 'Ventas (hist)', line: { color: '#60A5FA', width: 2 },
        marker: { size: 4, color: '#60A5FA' },
      });
      traces.push({
        x: hist.map(d => d[xKey]), y: hist.map(d => d.profit),
        type: 'scatter', mode: 'lines+markers', yaxis: 'y2',
        name: 'Utilidad (hist)', line: { color: '#34D399', width: 2 },
        marker: { size: 4, color: '#34D399' },
      });
    }
    if (fc.length) {
      traces.push({
        x: fc.map(d => d[xKey]), y: fc.map(d => d.sales),
        type: 'scatter', mode: 'lines+markers',
        name: 'Ventas (pron.)', line: { color: '#60A5FA', width: 2, dash: 'dash' },
        marker: { size: 5, color: '#60A5FA', symbol: 'diamond' },
      });
      traces.push({
        x: fc.map(d => d[xKey]), y: fc.map(d => d.profit),
        type: 'scatter', mode: 'lines+markers', yaxis: 'y2',
        name: 'Utilidad (pron.)', line: { color: '#34D399', width: 2, dash: 'dash' },
        marker: { size: 5, color: '#34D399', symbol: 'diamond' },
      });
    }
    R.plot(el, {
      data: traces,
      layout: {
        yaxis: { title: 'Ventas ($)' },
        yaxis2: { title: 'Utilidad ($)', overlaying: 'y', side: 'right' },
      },
    });
  },

  /* ── Predictor Info ──────────────────────────────────────── */
  mlPredictorInfo(container, info) {
    const r2 = info.r2 || 0;
    container.innerHTML = `
      <div class="callout-icon info">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
      </div>
      <div class="callout-body">
        <b>Predictor de Utilidad</b>
        <span>Modelo de regresion lineal entrenado sobre los datos historicos del negocio.
        R² = <strong>${r2.toFixed(3)}</strong>${r2 < 0.3 ? ' (bajo — la utilidad tiene alta varianza, pero las tendencias generales son utiles)' : r2 < 0.6 ? ' (moderado — las predicciones orientan correctamente)' : ' (bueno — el modelo explica bien la utilidad)'}.
        Ajusta los parametros en vivo — la prediccion se actualiza automaticamente al mover cualquier control.</span>
      </div>`;
  },

  /* ── Predictor Result (gauge) ────────────────────────────── */
  mlPredictorResult(container, result) {
    const profit = result.predicted_profit || 0;
    const isPos = profit >= 0;
    const range = Math.max(Math.abs(profit) * 1.5, 200);
    const pct = ((profit / range) * 50 + 50);
    const clampedPct = Math.max(4, Math.min(96, pct));
    const badgeCls = isPos ? 'gauge-badge-pos' : 'gauge-badge-neg';
    const badgeIcon = isPos
      ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>'
      : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
    container.innerHTML = `
      <div class="predictor-gauge animate-in">
        <div class="gauge-header">
          <span class="gauge-label">Utilidad Estimada</span>
          <span class="gauge-value ${isPos ? 'pos' : 'neg'}">${isPos ? '+' : '-'}$${Math.abs(profit).toFixed(2)}</span>
        </div>
        <div class="gauge-track">
          <div class="gauge-fill" style="width:${clampedPct}%;background:${isPos ? 'var(--neon-green)' : 'var(--neon-red)'}"></div>
          <div class="gauge-zero"></div>
        </div>
        <div class="gauge-labels">
          <span class="gauge-label-end">Perdida</span>
          <span class="gauge-label-mid">$0</span>
          <span class="gauge-label-end">Ganancia</span>
        </div>
        <div class="${badgeCls}">${badgeIcon} ${isPos ? 'Rentable' : 'No Rentable'}</div>
        <div class="gauge-meta">R² modelo: ${(result.model_r2 || 0).toFixed(3)}</div>
      </div>`;
  },

  /* ── Feature Importance Bars ──────────────────────────────── */
  mlFeatureImportance(el, features) {
    if (!features || !features.length) { el.innerHTML = ''; return; }
    const sorted = [...features].sort((a, b) => Math.abs(b.importance) - Math.abs(a.importance));
    const maxAbs = Math.max(...sorted.map(f => Math.abs(f.importance)), 1);
    el.innerHTML = '<div class="section-header"><div class="section-label">Importancia de Factores</div></div><div class="chart-card" style="padding:var(--space-4)">' +
      sorted.map(f => {
        const pct = (Math.abs(f.importance) / maxAbs * 100).toFixed(0);
        const cls = f.importance >= 0 ? '' : 'neg';
        return `<div class="feature-bar">
          <span class="lbl">${f.feature}</span>
          <span class="bar ${cls}" style="width:${pct}%"></span>
          <span class="val">${f.importance >= 0 ? '+' : ''}${f.importance.toFixed(4)}</span>
        </div>`;
      }).join('') +
    '</div>';
  },
};