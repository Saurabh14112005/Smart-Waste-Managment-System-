// CleanCity AI — app.js (Lavender Sidebar SPA)

const API_BASE = '';
const CITY_CENTER = [23.24, 77.44];
const DEPOT_LOCATION = [23.24, 77.45];

let map, markersLayer, routeLayer;
let currentRouteBinIds = [];
let autoTimer = null;
let currentActivePage = 'overview';

/* ─── Boot ──────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initMap();
  bindEvents();
  refresh();
  fetchComplaints();
});

/* ─── SPA Navigation ────────────────────────────────────── */
function initNavigation() {
  const links = document.querySelectorAll('.sb-link');
  const pages = document.querySelectorAll('.page');
  const title = document.getElementById('page-title');
  const sidebar = document.getElementById('sidebar');

  links.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      
      const targetPage = link.getAttribute('data-page');
      currentActivePage = targetPage;

      // Update active link
      links.forEach(l => l.classList.remove('active'));
      link.classList.add('active');

      // Update active section
      pages.forEach(p => p.classList.remove('active'));
      document.getElementById(`page-${targetPage}`).classList.add('active');

      // Update Top Bar Title
      title.textContent = link.querySelector('span').textContent;

      // Close sidebar on mobile
      sidebar.classList.remove('open');

      // Fix Leaflet container size bug when tab becomes visible
      if (targetPage === 'map' && map) {
        setTimeout(() => {
          map.invalidateSize();
        }, 100);
      }
    });
  });

  // Mobile Hamburger Toggle
  const toggleBtn = document.getElementById('btn-toggle-sidebar');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }

  // Close sidebar on body click (mobile)
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 840) {
      if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target) && sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
      }
    }
  });
}

/* ─── Leaflet Map ───────────────────────────────────────── */
function initMap() {
  map = L.map('map', { zoomControl: true, scrollWheelZoom: true })
         .setView(CITY_CENTER, 13);

  // Soft light theme map tiles matching lavender aesthetic
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 20
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);
  routeLayer = L.layerGroup().addTo(map);

  // Central Depot marker
  const depotIcon = L.divIcon({
    className: '',
    html: `<div style="width:14px;height:14px;background:#7c6fcd;border:2px solid #fff;border-radius:50%;box-shadow:0 0 8px rgba(124,111,205,0.6);"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7]
  });

  L.marker(DEPOT_LOCATION, { icon: depotIcon })
   .bindPopup('<b>Central Depot</b><br>Fleet starting point.')
   .addTo(map);
}

/* ─── Master Refresh ────────────────────────────────────── */
async function refresh() {
  const tenant = document.getElementById('tenant-filter').value.trim();
  const qs = tenant ? `?tenant_id=${encodeURIComponent(tenant)}` : '';

  await Promise.all([
    fetchHealth(),
    fetchTelemetry(qs),
    fetchRoute(qs)
  ]);

  const now = new Date();
  document.getElementById('last-sync-time').textContent =
    now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

/* ─── Health API (Check AI backend status) ──────────────── */
async function fetchHealth() {
  try {
    const d = await get('/health');
    const txtEl = document.getElementById('ai-status');
    const dotEl = document.getElementById('ai-dot');
    const modelStatusTxt = document.getElementById('model-status-txt');
    const modelStatusBox = document.getElementById('model-status-box');
    
    if (d.ai_engine === 'Ready') {
      const modeName = d.ai_backend.toUpperCase();
      txtEl.textContent = modeName;
      dotEl.className = 'sb-dot green';
      
      if (modelStatusTxt) {
        modelStatusTxt.textContent = `AI Engine Ready (${modeName} Mode)`;
        modelStatusBox.style.background = 'var(--green-soft)';
        modelStatusBox.style.borderColor = 'rgba(16,185,129,0.2)';
        modelStatusBox.querySelector('i').style.color = 'var(--green)';
      }
    } else {
      txtEl.textContent = 'OFFLINE';
      dotEl.className = 'sb-dot';
      
      if (modelStatusTxt) {
        modelStatusTxt.textContent = 'AI Model Offline. waste_model.h5 not found.';
        modelStatusBox.style.background = 'var(--red-soft)';
        modelStatusBox.style.borderColor = 'rgba(239,68,68,0.2)';
        modelStatusBox.querySelector('i').style.color = 'var(--red)';
      }
    }
  } catch (e) {
    console.error('Health fetch failed:', e);
  }
}

/* ─── Telemetry API ─────────────────────────────────────── */
async function fetchTelemetry(qs) {
  try {
    const bins = await get('/telemetry' + qs);
    updateKPIs(bins);
    renderTelemetryGrid(bins);
    renderMapMarkers(bins);
    renderAlerts(bins);
  } catch (e) {
    toast('Telemetry error: ' + e.message, 'err');
  }
}

function updateKPIs(bins) {
  const total = bins.length;
  const priority = bins.filter(b => b.fill_level >= 80).length;
  const mean = total ? (bins.reduce((s, b) => s + b.fill_level, 0) / total).toFixed(1) : '0.0';

  let latest = null;
  bins.forEach(b => {
    if (!b.last_update) return;
    const t = new Date(b.last_update);
    if (!latest || t > latest) latest = t;
  });

  document.getElementById('kpi-total').textContent = total;
  document.getElementById('kpi-priority').textContent = priority;
  document.getElementById('kpi-mean').textContent = mean + '%';
  document.getElementById('kpi-time').textContent = latest
    ? latest.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : '—';
}

function renderTelemetryGrid(bins) {
  const grid = document.getElementById('tele-grid');
  if (!bins.length) {
    grid.innerHTML = '<div class="placeholder">No telemetry data matching the current filter.</div>';
    return;
  }
  grid.innerHTML = bins.map(b => {
    const [color, badgeBg, badgeBorder] = fillColors(b.fill_level);
    const isDevice = b.status === 'Real';
    const modeColor = isDevice ? 'var(--cyan)' : 'var(--text-muted)';
    const modeLabel = isDevice ? '📡 DEVICE' : 'REGISTERED';
    return `
      <div class="bin-card">
        <div class="bin-top">
          <div>
            <div class="bin-name">${esc(b.location)}</div>
            <div class="bin-mode" style="color:${modeColor}">${modeLabel}</div>
          </div>
          <span class="bin-badge" style="background:${badgeBg};color:${color};border-color:${badgeBorder}">
            ${esc(b.status).toUpperCase()}
          </span>
        </div>
        <div class="bin-body">
          <div class="bin-fill" style="color:${color}">${b.fill_level}%</div>
          <div class="bin-stats">
            🔋 ${b.battery ?? '—'}%<br>
            🌡️ ${b.temp != null ? Number(b.temp).toFixed(1) : '—'}°C<br>
            💨 ${b.gas_level ?? '—'} ppm
          </div>
        </div>
      </div>`;
  }).join('');
}

function renderMapMarkers(bins) {
  markersLayer.clearLayers();
  bins.forEach(b => {
    if (b.lat == null || b.lon == null) return;
    const [color] = fillColors(b.fill_level);

    if (b.status === 'Real') {
      L.circleMarker([b.lat, b.lon], {
        radius: 18, color: 'rgba(6,182,212,.4)', weight: 1,
        fillColor: 'rgba(6,182,212,.05)', fillOpacity: 1
      }).addTo(markersLayer);
    }

    L.circleMarker([b.lat, b.lon], {
      radius: b.fill_level >= 80 ? 11 : 8,
      color, weight: 2, fillColor: color, fillOpacity: 0.75
    }).bindPopup(`
      <div style="font-family:'DM Sans',sans-serif;min-width:160px;">
        <strong style="font-family:'Space Grotesk',sans-serif">${esc(b.location)}</strong>
        <div style="margin:6px 0;font-size:.82rem;color:#4f46e5">Fill: <b style="color:${color}">${b.fill_level}%</b></div>
        <div style="font-size:.75rem;color:#6b7280">Mode: ${b.status === 'Real' ? '📡 Real Device' : '📋 Registered'}</div>
        <div style="font-size:.72rem;color:#aaa;margin-top:4px">${b.last_update ? b.last_update.slice(11,19) : '—'}</div>
      </div>
    `).addTo(markersLayer);
  });
}

function renderAlerts(bins) {
  const banner = document.getElementById('alert-banner');
  const bannerText = document.getElementById('alert-banner-text');
  
  const alertsCard = document.getElementById('alerts-card');
  const alertBadge = document.getElementById('alert-badge');
  const alertsBody = document.getElementById('alerts-body');

  const crit = bins.filter(b => {
    const s = String(b.status || '').toUpperCase();
    return b.fill_level >= 80 || s.includes('CRITICAL') || s.includes('FIRE') || s.includes('GAS');
  });
  const uniq = [...new Map(crit.map(b => [b.id, b])).values()];

  // 1. Global banner update
  if (uniq.length > 0) {
    banner.classList.remove('hidden');
    bannerText.innerHTML = `<strong>Attention Required:</strong> ${uniq.length} active alerts in municipal waste infrastructure. Empty priority bins immediately.`;
  } else {
    banner.classList.add('hidden');
  }

  // 2. Overview page widget update
  if (alertBadge) alertBadge.textContent = uniq.length;
  if (alertsBody) {
    if (uniq.length === 0) {
      alertsBody.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-circle-check"></i>
          <p>All bin fill levels and environment logs are within optimal boundaries.</p>
        </div>`;
    } else {
      alertsBody.innerHTML = `
        <div class="route-seq">
          ${uniq.slice(0, 6).map(b => {
            const cls = b.fill_level >= 80 ? 'crit' : 'warn';
            return `
              <div class="route-seq-item ${cls}">
                <div class="route-seq-num">!</div>
                <div class="route-seq-info">
                  <small>ALERT LEVEL HIGH · ${esc(b.location)}</small>
                  <span>Fill: <b>${b.fill_level}%</b> · Temp: ${b.temp ?? '—'}°C · Gas: ${b.gas_level ?? '—'} ppm</span>
                </div>
              </div>`;
          }).join('')}
        </div>`;
    }
  }
}

/* ─── Route API ─────────────────────────────────────────── */
async function fetchRoute(qs) {
  try {
    const data = await get('/route' + qs);
    const route = data.route || [];
    const m = data.metrics || {};

    const fillElem = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val || '—';
    };

    // Fill Map Page route widgets
    fillElem('r-dist', m.distance);
    fillElem('r-time', m.time);
    fillElem('r-co2', m.co2_kg_est);
    fillElem('r-fuel', m.fuel_liters_est);

    // Fill Overview Page route widgets
    fillElem('ov-dist', m.distance);
    fillElem('ov-time', m.time);
    fillElem('ov-co2', m.co2_kg_est);
    fillElem('ov-fuel', m.fuel_liters_est);

    routeLayer.clearLayers();
    currentRouteBinIds = route.map(b => b.id);

    const mapRouteList = document.getElementById('map-route-list');
    const ovRouteList = document.getElementById('ov-route-list');

    const renderRouteItems = () => {
      if (!route.length) {
        return '<div class="empty-route"><i class="fa-solid fa-circle-check"></i> No priority route required.</div>';
      }
      return route.map((b, i) => {
        const cls = b.fill_level >= 80 ? 'crit' : 'warn';
        const mode = b.status === 'Real' ? '📡 DEVICE' : 'REGISTERED';
        return `
          <div class="route-seq-item ${cls}">
            <div class="route-seq-num">${i + 1}</div>
            <div class="route-seq-info">
              <small>${mode}</small>
              <span>📍 ${esc(b.location)} (<b>${b.fill_level}%</b>)</span>
            </div>
          </div>`;
      }).join('');
    };

    const markup = renderRouteItems();
    if (mapRouteList) mapRouteList.innerHTML = markup;
    if (ovRouteList) ovRouteList.innerHTML = markup;

    // Draw route overlay line on map
    if (route.length) {
      const pts = [DEPOT_LOCATION, ...route.map(b => [b.lat, b.lon])];
      L.polyline(pts, {
        color: '#7c6fcd', weight: 4, opacity: 0.85,
        dashArray: '8 14', lineCap: 'round'
      }).addTo(routeLayer);
    }

  } catch (e) {
    console.warn('Route engine sync failure:', e);
  }
}

/* ─── Dispatch Collection ───────────────────────────────── */
async function dispatch() {
  if (!currentRouteBinIds.length) {
    toast('No priority bins loaded in current routing model.', 'warn');
    return;
  }
  try {
    const d = await post('/bins/reset', { bin_ids: currentRouteBinIds });
    toast(`🚚 ${d.message}`);
    setTimeout(refresh, 1000);
  } catch (e) {
    toast('Collection dispatch fail: ' + e.message, 'err');
  }
}

/* ─── AI Vision classification ──────────────────────────── */
async function runVision(file) {
  if (!file?.type.startsWith('image/')) {
    toast('Please select a valid image sample.', 'warn');
    return;
  }

  const preview = document.getElementById('v-preview');
  const img = document.getElementById('v-img');
  const result = document.getElementById('v-result');
  const idleBox = document.getElementById('v-idle');

  // Preview file local URL
  const reader = new FileReader();
  reader.onload = e => {
    img.src = e.target.result;
    preview.classList.remove('hidden');
  };
  reader.readAsDataURL(file);

  if (idleBox) idleBox.classList.add('hidden');
  result.classList.remove('hidden');
  result.innerHTML = '<div class="vision-spinner"><i class="fa-solid fa-gear fa-spin"></i> Running inference model…</div>';

  const form = new FormData();
  form.append('file', file);

  try {
    const res = await fetch('/predict', { method: 'POST', body: form });
    
    if (res.status === 503) {
      result.innerHTML = `
        <div style="color:var(--orange);font-size:0.83rem;">
          <i class="fa-solid fa-circle-exclamation"></i> 
          <strong>AI Model Offline:</strong> Keras model failed to load. 
          Please place model file in <code>ai_engine/models/waste_model.h5</code> and check server logs.
        </div>`;
      return;
    }
    
    if (!res.ok) throw new Error('Model return status code ' + res.status);
    
    const d = await res.json();
    const pct = (d.confidence * 100).toFixed(1);
    
    result.innerHTML = `
      <small>Waste Segment Diagnostics</small>
      <h3>${esc(d.label)}</h3>
      <h2>${pct}%</h2>
      <p><strong>Guidance:</strong> ${esc(d.guidance)}</p>
      <hr>
      <small style="color:var(--text-muted)">Inference Pipeline Speed: ${d.inference_time} ms</small>`;
      
  } catch (e) {
    result.innerHTML = `<div style="color:var(--red);font-size:0.83rem;"><i class="fa-solid fa-triangle-exclamation"></i> Pipeline failed: ${esc(e.message)}</div>`;
  }
}

/* ─── Complaints API ────────────────────────────────────── */
async function fetchComplaints() {
  try {
    const rows = await get('/complaints?limit=10');
    const tbody = document.querySelector('#ct-table tbody');
    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="ct-empty">No community logs reported.</td></tr>`;
      return;
    }
    tbody.innerHTML = rows.map((r, i) => `
      <tr>
        <td><b>${i + 1}</b></td>
        <td>${esc(r.Citizen || r.user_name)}</td>
        <td>${esc(r.Location || r.location)}</td>
        <td>${esc(r.Issue || r.type)}</td>
        <td><span class="badge-pending">${esc(r.Status || r.status)}</span></td>
        <td><small style="color:var(--text-muted)">${esc(r.Timestamp || r.timestamp)}</small></td>
      </tr>`).join('');
  } catch (_) {
    console.warn('Error syncing complaints.');
  }
}

async function submitComplaint(e) {
  e.preventDefault();
  const name = document.getElementById('c-name').value.trim();
  const loc = document.getElementById('c-loc').value.trim();
  const type = document.getElementById('c-type').value;
  try {
    await post('/complaints', { user_name: name, location: loc, type });
    toast('Intelligence report registered successfully!');
    e.target.reset();
    fetchComplaints();
  } catch (err) {
    toast('Unable to process complaint submission.', 'err');
  }
}

/* ─── Event Bindings ────────────────────────────────────── */
function bindEvents() {
  // Global actions
  document.getElementById('btn-refresh').addEventListener('click', refresh);
  
  // Filter apply
  document.getElementById('btn-apply-filter').addEventListener('click', () => {
    refresh();
    toast('Filter applied');
  });
  document.getElementById('tenant-filter').addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      refresh();
      toast('Filter applied');
    }
  });

  // Dispatch buttons (available on both Overview and Map tabs)
  document.getElementById('btn-dispatch-ov').addEventListener('click', dispatch);
  document.getElementById('btn-dispatch-map').addEventListener('click', dispatch);

  // Complaints
  document.getElementById('complaint-form').addEventListener('submit', submitComplaint);
  document.getElementById('btn-refresh-complaints').addEventListener('click', () => {
    fetchComplaints();
    toast('Complaints refreshed');
  });

  // Upload/AI Area drag-and-drop
  const zone = document.getElementById('upload-zone');
  const finput = document.getElementById('file-input');
  
  zone.addEventListener('click', () => finput.click());
  
  zone.addEventListener('dragover', e => {
    e.preventDefault();
    zone.style.borderColor = 'var(--lavender)';
    zone.style.background = 'var(--lavender-lt)';
  });
  
  zone.addEventListener('dragleave', () => {
    zone.style.borderColor = '';
    zone.style.background = '';
  });
  
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.style.borderColor = '';
    zone.style.background = '';
    if (e.dataTransfer.files[0]) {
      runVision(e.dataTransfer.files[0]);
    }
  });
  
  finput.addEventListener('change', e => {
    if (e.target.files[0]) {
      runVision(e.target.files[0]);
    }
  });

  // Auto-refresh switcher
  document.getElementById('auto-refresh-toggle').addEventListener('change', e => {
    if (e.target.checked) {
      autoTimer = setInterval(refresh, 5000);
      toast('Auto-sync system active (5s interval)');
    } else {
      clearInterval(autoTimer);
      autoTimer = null;
      toast('Auto-sync deactivated');
    }
  });
}

/* ─── Fetch Wrapper Helpers ─────────────────────────────── */
async function get(url) {
  const r = await fetch(API_BASE + url);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return r.json();
}
async function post(url, body) {
  const r = await fetch(API_BASE + url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return r.json();
}

function fillColors(pct) {
  if (pct >= 80) return ['var(--red)', 'var(--red-soft)', 'rgba(239,68,68,0.2)'];
  if (pct >= 60) return ['var(--orange)', 'var(--orange-soft)', 'rgba(245,158,11,0.2)'];
  return ['var(--green)', 'var(--green-soft)', 'rgba(16,185,129,0.2)'];
}

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function toast(msg, type = 'ok') {
  const wrap = document.getElementById('toast-wrap');
  const el = document.createElement('div');
  const icon = type === 'err' ? 'fa-circle-xmark' : type === 'warn' ? 'fa-triangle-exclamation' : 'fa-circle-check';
  
  el.className = `toast ${type === 'err' ? 'err' : type === 'warn' ? 'warn' : ''}`;
  el.innerHTML = `<i class="fa-solid ${icon}"></i> ${msg}`;
  wrap.appendChild(el);
  
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(10px)';
    el.style.transition = 'all 0.4s ease';
    setTimeout(() => el.remove(), 400);
  }, 3500);
}
