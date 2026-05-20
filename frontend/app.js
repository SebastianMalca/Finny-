// ═══════════════════════════════════════════════════════════════
// FINNY Finance App — Frontend v3
// Dark dashboard with Auth: login, registro, recuperación de contraseña.
// ═══════════════════════════════════════════════════════════════

const API = 'http://localhost:5000';

// ── Category config ───────────────────────────────────────────
const CAT = {
  Food:          { color: '#f97316', label: '🍔 Comida' },
  Transport:     { color: '#38bdf8', label: '🚌 Transporte' },
  Study:         { color: '#4ade80', label: '📚 Estudio' },
  Entertainment: { color: '#c084fc', label: '🎮 Entretenimiento' },
  Health:        { color: '#f472b6', label: '❤️ Salud' },
  Other:         { color: '#94a3b8', label: '📦 Otro' },
};

const CAT_COLORS = Object.fromEntries(Object.entries(CAT).map(([k, v]) => [k, v.color]));

// ── Chart instances ───────────────────────────────────────────
let chartTrendDash      = null;
let chartTrendAnalytics = null;
let chartDonut          = null;

// ── State ─────────────────────────────────────────────────────
let activeSection    = 'dashboard';
let gFilter          = '';   // current category filter in gastos
let currentDashboard = null; // last dashboard API response
let currentUser      = null; // logged-in user info

// ═══════════════════════════════════════════════════════════════
// BOOT — Check session, then show auth or app
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', async () => {
  setupNavigation();
  setupForms();
  setupFilterChips();
  setupAuthKeyboardShortcuts();
  await checkSession();
});

async function checkSession() {
  try {
    const data   = await api('GET', '/auth/me');
    currentUser  = data.user;
    showApp();
  } catch (e) {
    showAuthScreen();
  }
}

function showApp() {
  document.getElementById('auth-screen').classList.remove('visible');
  document.getElementById('app').style.display = 'grid';
  refreshAll();
}

function showAuthScreen() {
  document.getElementById('auth-screen').classList.add('visible');
  document.getElementById('app').style.display = 'none';
}

async function refreshAll() {
  await Promise.all([
    loadDashboard(),
    loadRightPanelActivity(),
    loadRightPanelTips(),
  ]);
  updateMissionsBadge();
}

// ═══════════════════════════════════════════════════════════════
// AUTH — Login / Register / Logout / Forgot Password
// ═══════════════════════════════════════════════════════════════

function switchAuthTab(tab) {
  ['login', 'register'].forEach(t => {
    document.getElementById(`tab-${t}`).classList.toggle('active', t === tab);
    document.getElementById(`panel-${t}`).classList.toggle('active', t === tab);
  });
  clearAuthErrors();
}

function clearAuthErrors() {
  ['login-error', 'register-error', 'forgot-error', 'forgot-success',
   'reset-error', 'reset-success'].forEach(id => {
    const el = document.getElementById(id);
    if (el) { el.textContent = ''; el.classList.remove('show'); }
  });
}

function showForgotPassword() {
  document.getElementById('auth-main-card').style.display = 'none';
  document.getElementById('auth-forgot-card').style.display = 'block';
  clearAuthErrors();
}

function hideForgotPassword() {
  document.getElementById('auth-forgot-card').style.display = 'none';
  document.getElementById('auth-main-card').style.display = 'block';
  clearAuthErrors();
}

function setupAuthKeyboardShortcuts() {
  document.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      const panel = document.querySelector('.auth-panel.active');
      if (panel?.id === 'panel-login')    doLogin();
      if (panel?.id === 'panel-register') doRegister();
    }
  });
}

async function doLogin() {
  const email    = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  const errEl    = document.getElementById('login-error');
  const btn      = document.getElementById('btn-login');

  if (!email || !password) {
    errEl.textContent = 'Por favor completa todos los campos.';
    errEl.classList.add('show');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Iniciando…';
  errEl.classList.remove('show');

  try {
    const data  = await api('POST', '/auth/login', { email, password });
    currentUser = data.user;
    toast(`👋 ¡Bienvenido, ${data.user.username}!`, 'success');
    document.getElementById('login-password').value = '';
    showApp();
  } catch (e) {
    errEl.textContent = e.message || 'Email o contraseña incorrectos.';
    errEl.classList.add('show');
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Iniciar sesión';
  }
}

async function doRegister() {
  const username = document.getElementById('reg-username').value.trim();
  const email    = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  const errEl    = document.getElementById('register-error');
  const btn      = document.getElementById('btn-register');

  if (!username || !email || !password) {
    errEl.textContent = 'Por favor completa todos los campos.';
    errEl.classList.add('show');
    return;
  }
  if (password.length < 8) {
    errEl.textContent = 'La contraseña debe tener al menos 8 caracteres.';
    errEl.classList.add('show');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Creando cuenta…';
  errEl.classList.remove('show');

  try {
    const data  = await api('POST', '/auth/register', { username, email, password });
    currentUser = data.user;
    toast(`🎉 ¡Bienvenido a FINNY, ${data.user.username}!`, 'success');
    document.getElementById('reg-password').value = '';
    showApp();
  } catch (e) {
    errEl.textContent = e.message || 'Error al crear la cuenta.';
    errEl.classList.add('show');
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Crear cuenta';
  }
}

async function doLogout() {
  try {
    await api('POST', '/auth/logout');
  } catch (e) { /* always log out locally */ }
  currentUser = null;
  toast('👋 Sesión cerrada. ¡Hasta pronto!', 'info');
  showAuthScreen();
}

async function doForgotPassword() {
  const email  = document.getElementById('forgot-email').value.trim();
  const errEl  = document.getElementById('forgot-error');
  const okEl   = document.getElementById('forgot-success');
  const tokEl  = document.getElementById('forgot-token');
  const btn    = document.getElementById('btn-forgot');

  errEl.classList.remove('show');
  okEl.classList.remove('show');
  tokEl.classList.remove('show');

  if (!email) {
    errEl.textContent = 'Ingresa tu email.';
    errEl.classList.add('show');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Enviando…';

  try {
    const data = await api('POST', '/auth/forgot-password', { email });
    okEl.textContent = data.message;
    okEl.classList.add('show');

    if (data.debug_token) {
      tokEl.textContent = '🔑 Token (modo demo): ' + data.debug_token;
      tokEl.classList.add('show');
      document.getElementById('reset-token-input').value = data.debug_token;
      document.getElementById('reset-form-section').style.display = 'block';
    }
  } catch (e) {
    errEl.textContent = e.message || 'Error al procesar la solicitud.';
    errEl.classList.add('show');
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Enviar token';
  }
}

async function doResetPassword() {
  const token    = document.getElementById('reset-token-input').value.trim();
  const password = document.getElementById('reset-new-password').value;
  const errEl    = document.getElementById('reset-error');
  const okEl     = document.getElementById('reset-success');
  const btn      = document.getElementById('btn-reset');

  errEl.classList.remove('show');
  okEl.classList.remove('show');

  if (!token || !password) {
    errEl.textContent = 'Completa el token y la nueva contraseña.';
    errEl.classList.add('show');
    return;
  }
  if (password.length < 8) {
    errEl.textContent = 'La contraseña debe tener al menos 8 caracteres.';
    errEl.classList.add('show');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Cambiando…';

  try {
    const data = await api('POST', '/auth/reset-password', { token, password });
    okEl.textContent = data.message + ' Redirigiendo al login…';
    okEl.classList.add('show');
    setTimeout(() => {
      hideForgotPassword();
      switchAuthTab('login');
    }, 2500);
  } catch (e) {
    errEl.textContent = e.message || 'Token inválido o expirado.';
    errEl.classList.add('show');
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Cambiar contraseña';
  }
}

// ═══════════════════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════════════════

function setupNavigation() {
  document.querySelectorAll('.nav-item[data-section]').forEach(btn => {
    btn.addEventListener('click', () => navigateTo(btn.dataset.section));
  });
}

function navigateTo(section) {
  activeSection = section;

  // Toggle sections
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  const el = document.getElementById(`section-${section}`);
  if (el) el.classList.add('active');

  // Toggle nav items
  document.querySelectorAll('.nav-item').forEach(b => {
    b.classList.toggle('active', b.dataset.section === section);
  });

  // Lazy-load section data
  if (section === 'gastos')    loadGastos();
  if (section === 'analytics') loadAnalytics();
  if (section === 'misiones')  loadMisiones();
  if (section === 'logros')    loadLogros();
  if (section === 'config')    loadConfig();
}

// ═══════════════════════════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════════════════════════

async function loadDashboard() {
  try {
    const data = await api('GET', '/dashboard');
    currentDashboard = data;

    // Update profile UI everywhere
    updateProfileUI(data.profile);

    // Balance card
    updateBalanceCard(data);

    // Budget progress
    updateBudgetProgress(data);

    // Stats row
    setText('today-spent', fmt(data.today_spent));
    setText('week-spent',  fmt(data.week_spent));
    const diff = data.today_vs_yesterday;
    const diffEl = document.getElementById('today-vs-yesterday');
    if (diffEl) {
      if (diff > 0) {
        diffEl.style.color = '#f97316';
        diffEl.textContent = `▲ $${diff.toFixed(2)} vs ayer`;
      } else if (diff < 0) {
        diffEl.style.color = '#4ade80';
        diffEl.textContent = `▼ $${Math.abs(diff).toFixed(2)} vs ayer`;
      } else {
        diffEl.textContent = 'igual que ayer';
        diffEl.style.color = '#64748b';
      }
    }

    // Streak
    updateStreakUI(data.streak);

    // Trend chart (dashboard)
    renderTrendChart('chart-trend-dash', data.trend, chartTrendDash, c => chartTrendDash = c);

    // Active missions
    renderMissionCards(data.missions_active, 'dash-missions');

    // Right panel mini stats
    setText('rp-streak-mini', data.streak?.current_streak ?? 0);
    setText('rp-week',        '$' + (data.week_spent ?? 0).toFixed(0));

    // Alert banner
    updateAlertBanner(data);

    // Name greeting
    setText('dash-name', data.profile?.name ?? 'Joven');

  } catch (err) {
    console.error('Dashboard error:', err);
  }
}

function updateBalanceCard(data) {
  const card = document.getElementById('balance-card');
  const amountEl = document.getElementById('balance-amount');
  if (!card || !amountEl) return;

  // Remove alert classes
  card.classList.remove('alert-low', 'alert-overspent');

  if (!data.budget) {
    amountEl.textContent = 'Sin presupuesto';
    amountEl.style.fontSize = '1.8rem';
  } else if (data.overspent) {
    card.classList.add('alert-overspent');
    amountEl.textContent = `-${fmt(data.month_spent - data.budget)}`;
    amountEl.style.fontSize = '2.4rem';
  } else if (data.alert_mode) {
    card.classList.add('alert-low');
    amountEl.textContent = fmt(data.remaining);
    amountEl.style.fontSize = '2.4rem';
  } else {
    amountEl.textContent = fmt(data.remaining);
    amountEl.style.fontSize = '2.8rem';
  }

  setText('days-remaining',   data.days_remaining);
  setText('daily-available',  fmt(data.daily_available));
  setText('month-spent',      fmt(data.month_spent));
}

function updateBudgetProgress(data) {
  const fill        = document.getElementById('budget-fill');
  const pctLabel    = document.getElementById('budget-pct-label');
  const totalLabel  = document.getElementById('budget-total-label');
  const spentLabel  = document.getElementById('budget-spent-label');
  const ofLabel     = document.getElementById('budget-of-label');
  const noHint      = document.getElementById('no-budget-hint');

  if (!data.budget) {
    if (noHint) noHint.style.display = 'block';
    if (fill)   fill.style.width = '0%';
    return;
  }
  if (noHint) noHint.style.display = 'none';

  const pct = Math.min(100, data.budget_used_pct);
  if (fill) {
    fill.style.width = pct + '%';
    fill.classList.remove('warning', 'danger');
    if (data.overspent)       fill.classList.add('danger');
    else if (data.alert_mode) fill.classList.add('warning');
  }
  if (pctLabel)   pctLabel.textContent = pct.toFixed(1) + '%';
  if (totalLabel) totalLabel.textContent = fmt(data.budget);
  if (spentLabel) spentLabel.textContent = `Gastado: ${fmt(data.month_spent)}`;
  if (ofLabel)    ofLabel.textContent = fmt(data.budget);
}

function updateAlertBanner(data) {
  const banner = document.getElementById('alert-banner');
  const text   = document.getElementById('alert-banner-text');
  const icon   = document.getElementById('alert-banner-icon');
  if (!banner) return;

  if (data.overspent) {
    const extra = (data.month_spent - data.budget).toFixed(2);
    banner.className = 'danger';
    icon.textContent = '🚨';
    text.textContent = `¡Superaste tu presupuesto por $${extra}! Considera pausar los gastos no esenciales.`;
    document.querySelector('.main-content').style.paddingTop = '60px';
  } else if (data.alert_mode) {
    banner.className = 'warning';
    icon.textContent = '⚠️';
    text.textContent = `Modo Alerta — Solo te quedan ${fmt(data.remaining)} para ${data.days_remaining} días. Límite diario: ${fmt(data.daily_available)}.`;
    document.querySelector('.main-content').style.paddingTop = '60px';
  } else {
    banner.className = 'hidden';
    document.querySelector('.main-content').style.paddingTop = '28px';
  }
}

function updateStreakUI(streak) {
  if (!streak) return;
  const count = streak.current_streak;
  setText('streak-count', count);

  // Flame animation: bigger when streak is active
  const flame = document.getElementById('streak-flame');
  if (flame) flame.style.display = count > 0 ? 'inline' : 'inline';

  const longest = document.getElementById('streak-longest');
  if (longest) longest.textContent = `Mejor racha: ${streak.longest_streak} días · Total activos: ${streak.total_active_days}`;

  // 7-day dots
  const row = document.getElementById('streak-days-row');
  if (!row) return;
  row.innerHTML = '';
  const today = new Date();
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today); d.setDate(today.getDate() - i);
    const label = d.toLocaleDateString('es', { weekday: 'narrow' });
    const div   = document.createElement('div');
    div.className = 'streak-day';
    div.textContent = label;
    if (i === 0 && streak.last_active_date === d.toISOString().split('T')[0]) {
      div.classList.add('today');
    } else if (streak.last_active_date && i > 0) {
      const dayStr = d.toISOString().split('T')[0];
      const last   = new Date(streak.last_active_date);
      const tdiff  = Math.floor((last - d) / 86400000);
      if (tdiff >= 0 && tdiff < count) div.classList.add('done');
    }
    row.appendChild(div);
  }
}

function updateProfileUI(profile) {
  if (!profile) return;
  const lvl = profile.level;

  // Sidebar mini
  setText('sb-name',   profile.name);
  setText('sb-level',  `Nivel ${lvl} · ${profile.xp} XP`);
  setText('sb-avatar', profile.avatar || profile.name?.slice(0,2).toUpperCase() || 'JV');

  // Dashboard
  setText('profile-level',    lvl);
  setText('profile-name-level', `Nivel ${lvl}`);
  setText('profile-xp',       profile.xp_progress ?? 0);
  setText('profile-xp-next',  profile.xp_for_next ?? 200);
  const xpFill = document.getElementById('xp-bar-fill');
  if (xpFill) xpFill.style.width = (profile.xp_pct ?? 0) + '%';

  // Right panel
  const avText = profile.avatar || profile.name?.slice(0,2).toUpperCase() || 'JV';
  setText('rp-avatar', avText);
  setText('rp-name',   profile.name);
  setText('rp-level',  `Nivel ${lvl} — ${levelTitle(lvl)}`);
  setText('rp-xp',     `${profile.xp_progress ?? 0} / ${profile.xp_for_next ?? 200} XP`);
  const rpBar = document.getElementById('rp-xp-bar');
  if (rpBar) rpBar.style.width = (profile.xp_pct ?? 0) + '%';
  setText('rp-level-mini', lvl);
}

function levelTitle(lvl) {
  const titles = ['','Novato','Aprendiz','Curioso','Talento','Experto','Maestro','Gurú','Leyenda'];
  return titles[Math.min(lvl, titles.length - 1)] ?? 'Élite';
}

// ═══════════════════════════════════════════════════════════════
// TREND CHART
// ═══════════════════════════════════════════════════════════════

function renderTrendChart(canvasId, trendData, existingChart, setter) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const labels = trendData.map(d => d.short ?? d.label);
  const values = trendData.map(d => d.total);

  if (existingChart) existingChart.destroy();

  const gradient = canvas.getContext('2d').createLinearGradient(0, 0, 0, 200);
  gradient.addColorStop(0,   'rgba(79,172,254,0.3)');
  gradient.addColorStop(1,   'rgba(79,172,254,0)');

  const chart = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Gasto ($)',
        data: values,
        borderColor: '#4facfe',
        backgroundColor: gradient,
        borderWidth: 2.5,
        fill: true,
        tension: 0.45,
        pointBackgroundColor: '#4facfe',
        pointBorderColor:     '#060914',
        pointBorderWidth:     2,
        pointRadius:          5,
        pointHoverRadius:     7,
      }]
    },
    options: chartOptions('$'),
  });
  setter(chart);
}

function chartOptions(prefix = '$') {
  return {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(13,17,40,0.95)',
        borderColor: 'rgba(79,172,254,.3)', borderWidth: 1,
        titleColor: '#94a3b8', bodyColor: '#f1f5f9',
        padding: 12, cornerRadius: 10,
        callbacks: { label: ctx => `  ${prefix}${ctx.raw.toFixed(2)}` }
      },
    },
    scales: {
      x: {
        grid:  { color: 'rgba(255,255,255,0.04)', drawBorder: false },
        ticks: { color: '#64748b', font: { size: 11 } },
      },
      y: {
        grid:  { color: 'rgba(255,255,255,0.04)', drawBorder: false },
        ticks: { color: '#64748b', font: { size: 11 }, callback: v => `$${v}` },
        beginAtZero: true,
      }
    },
    interaction: { mode: 'index', intersect: false },
  };
}

// ═══════════════════════════════════════════════════════════════
// ANALYTICS SECTION
// ═══════════════════════════════════════════════════════════════

async function loadAnalytics() {
  await Promise.all([loadTrend(7), loadDonut()]);
}

let currentTrendDays = 7;
async function loadTrend(days) {
  currentTrendDays = days;
  // Update chip styles
  [7, 14, 30].forEach(d => {
    const btn = document.getElementById(`trend-${d}`);
    if (btn) btn.classList.toggle('active', d === days);
  });
  try {
    const data = await api('GET', `/tendencia?days=${days}`);
    renderTrendChart('chart-trend-analytics', data.trend, chartTrendAnalytics, c => chartTrendAnalytics = c);
  } catch(e) { console.error(e); }
}

async function loadDonut() {
  try {
    const data    = await api('GET', '/estadisticas');
    const cats    = data.by_category;
    const canvas  = document.getElementById('chart-donut');
    if (!canvas || !cats.length) return;

    if (chartDonut) chartDonut.destroy();

    const labels = cats.map(c => c.category);
    const values = cats.map(c => c.total);
    const colors = cats.map(c => CAT_COLORS[c.category] ?? '#64748b');

    chartDonut = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: colors.map(c => c + '99'),
          borderColor:     colors,
          borderWidth:     2,
          hoverBorderWidth: 3,
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#94a3b8', font: { size: 11 }, padding: 14, usePointStyle: true }
          },
          tooltip: {
            backgroundColor: 'rgba(13,17,40,0.95)',
            borderColor: 'rgba(255,255,255,.1)', borderWidth: 1,
            titleColor: '#94a3b8', bodyColor: '#f1f5f9',
            callbacks: { label: ctx => `  $${ctx.raw.toFixed(2)}` }
          },
        }
      }
    });

    // Analytics stats sidebar
    const statsEl = document.getElementById('analytics-stats');
    if (statsEl) {
      statsEl.innerHTML = '';
      cats.forEach(c => {
        const color = CAT_COLORS[c.category] ?? '#64748b';
        const cat   = CAT[c.category];
        const div   = document.createElement('div');
        div.style.cssText = `background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:12px;border-left:3px solid ${color};`;
        div.innerHTML = `
          <div style="font-size:.75rem;color:${color};font-weight:700;margin-bottom:4px;">${cat?.label ?? c.category}</div>
          <div style="font-size:1.05rem;font-weight:800;">$${c.total.toFixed(2)}</div>
          <div style="font-size:.7rem;color:#64748b;margin-top:3px;">${c.count} gasto${c.count!==1?'s':''} · prom $${c.average.toFixed(2)}</div>
        `;
        statsEl.appendChild(div);
      });
    }
  } catch(e) { console.error(e); }
}

// ═══════════════════════════════════════════════════════════════
// GASTOS SECTION
// ═══════════════════════════════════════════════════════════════

async function loadGastos() {
  try {
    const url  = gFilter ? `/compras?category=${encodeURIComponent(gFilter)}` : '/compras';
    const data = await api('GET', url);
    renderGastosList(data.purchases, data.total);
    setText('rp-count', data.count);
  } catch(e) { console.error(e); }
}

function renderGastosList(purchases, total) {
  const list    = document.getElementById('g-list');
  const cntEl   = document.getElementById('g-count');
  const totalEl = document.getElementById('g-total');
  const rowEl   = document.getElementById('g-total-row');

  if (!list) return;
  if (cntEl) cntEl.textContent = `${purchases.length} gasto${purchases.length!==1?'s':''}`;

  if (!purchases.length) {
    list.innerHTML = `<li class="empty-state"><div class="empty-icon">🛍️</div>No hay gastos${gFilter ? ` en "${gFilter}"` : ''} aún.</li>`;
    if (rowEl) rowEl.style.setProperty('display','none','important');
    return;
  }

  list.innerHTML = '';
  purchases.forEach(p => {
    const color = CAT_COLORS[p.category] ?? '#94a3b8';
    const li    = document.createElement('li');
    li.className = 'purchase-item';
    li.innerHTML = `
      <span class="cat-dot" style="color:${color};background:${color};"></span>
      <div class="purchase-info">
        <div class="purchase-name">${esc(p.name)}</div>
        <div class="purchase-meta">${p.category} · ${fmtDate(p.created_at)}</div>
      </div>
      <div class="purchase-amount">$${p.amount.toFixed(2)}</div>
      <button class="purchase-del" title="Eliminar" onclick="deletePurchase(${p.id},'${esc(p.name)}')">✕</button>
    `;
    list.appendChild(li);
  });

  if (totalEl) totalEl.textContent = `$${total.toFixed(2)}`;
  if (rowEl)   rowEl.style.setProperty('display','flex','important');
}

async function deletePurchase(id, name) {
  if (!confirm(`¿Eliminar "${name}"?`)) return;
  try {
    await api('DELETE', `/compras/${id}`);
    toast(`🗑️ "${name}" eliminado`, 'info');
    loadGastos();
    loadDashboard();
    loadRightPanelActivity();
  } catch(e) {
    toast('Error al eliminar', 'error');
  }
}

function setupFilterChips() {
  const bar = document.getElementById('g-filters');
  if (!bar) return;
  bar.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      bar.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      gFilter = chip.dataset.cat;
      loadGastos();
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// FORMS (quick add)
// ═══════════════════════════════════════════════════════════════

function setupForms() {
  // Dashboard form
  const dashForm = document.getElementById('dash-form');
  if (dashForm) dashForm.addEventListener('submit', e => submitPurchase(e, 'dash'));

  // Gastos form
  const gForm = document.getElementById('g-form');
  if (gForm) gForm.addEventListener('submit', e => submitPurchase(e, 'g'));
}

async function submitPurchase(e, prefix) {
  e.preventDefault();

  const name     = document.getElementById(`${prefix}-name`).value.trim();
  const amount   = parseFloat(document.getElementById(`${prefix}-amount`).value);
  const category = document.getElementById(`${prefix}-cat`)?.value || 'Other';

  hideAlert(prefix + '-error');
  hideAlert(prefix + '-success');

  if (!name)            return showAlert(prefix + '-error', '⚠️ El nombre es requerido.');
  if (!amount || amount <= 0) return showAlert(prefix + '-error', '⚠️ El monto debe ser mayor a 0.');

  setLoading(prefix, true);
  try {
    const res = await api('POST', '/compras', { name, amount, category });
    showAlert(prefix + '-success', `✅ "${name}" agregado · +5 XP`);
    document.getElementById(`${prefix}-name`).value = '';
    document.getElementById(`${prefix}-amount`).value = '';

    // Check for missions/achievements in background
    toast(`💸 Gasto registrado — +5 XP`, 'success');

    await Promise.all([
      loadDashboard(),
      loadRightPanelActivity(),
    ]);
    if (activeSection === 'gastos') loadGastos();
    updateMissionsBadge();

  } catch(err) {
    showAlert(prefix + '-error', '❌ ' + (err.message ?? 'Error al agregar gasto.'));
  } finally {
    setLoading(prefix, false);
  }
}

// ═══════════════════════════════════════════════════════════════
// MISIONES
// ═══════════════════════════════════════════════════════════════

async function loadMisiones() {
  const data = await api('GET', '/misiones');
  const active = data.missions.filter(m => !m.completed);
  const done   = data.missions.filter(m => m.completed);
  renderMissionCards(active, 'missions-active');
  renderMissionCards(done,   'missions-done');
  updateMissionsBadge(active.length);
}

function renderMissionCards(missions, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;

  if (!missions.length) {
    el.innerHTML = `<div class="empty-state" style="padding:20px;"><div class="empty-icon" style="font-size:1.5rem;">🎯</div>Nada aquí aún.</div>`;
    return;
  }

  el.innerHTML = '';
  missions.forEach(m => {
    const card = document.createElement('div');
    card.className = 'mission-card' + (m.completed ? ' done' : '');
    card.innerHTML = `
      <div class="mission-icon-wrap">${m.icon}</div>
      <div class="mission-body">
        <div class="mission-title">${esc(m.title)}</div>
        <div class="mission-desc">${esc(m.description)}</div>
        <div class="mission-progress">
          <div class="mission-progress-fill" style="width:${m.progress_pct ?? 0}%"></div>
        </div>
        <div class="mission-footer">
          <span class="mission-xp">+${m.reward_xp} XP</span>
          <span class="mission-pct">${m.completed ? '✅ Completada' : `${m.current_value}/${m.target_value}`}</span>
        </div>
      </div>
    `;
    el.appendChild(card);
  });
}

async function updateMissionsBadge(count = null) {
  try {
    if (count === null) {
      const data = await api('GET', '/misiones');
      count = data.missions.filter(m => !m.completed).length;
    }
    const badge = document.getElementById('badge-misiones');
    if (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    }
  } catch(e) { /* silent */ }
}

// ═══════════════════════════════════════════════════════════════
// LOGROS
// ═══════════════════════════════════════════════════════════════

async function loadLogros() {
  const data = await api('GET', '/logros');
  const grid = document.getElementById('achievements-grid');
  if (!grid) return;
  grid.innerHTML = '';

  data.achievements.forEach(a => {
    const badge = document.createElement('div');
    badge.className = 'achievement-badge ' + (a.unlocked ? 'unlocked' : 'locked');
    badge.innerHTML = `
      <span class="badge-icon">${a.icon}</span>
      <div class="badge-title">${esc(a.title)}</div>
      <div class="badge-desc">${esc(a.description)}</div>
      ${a.unlocked ? `<div class="badge-unlocked-tag">✓ Desbloqueado</div>` : '<div class="badge-unlocked-tag">🔒 Bloqueado</div>'}
    `;
    grid.appendChild(badge);
  });
}

// ═══════════════════════════════════════════════════════════════
// RIGHT PANEL
// ═══════════════════════════════════════════════════════════════

async function loadRightPanelActivity() {
  try {
    const data = await api('GET', '/compras');
    const list  = document.getElementById('rp-activity');
    if (!list) return;

    const recent = data.purchases.slice(0, 5);
    setText('rp-count', data.count);

    if (!recent.length) {
      list.innerHTML = `<div class="text-muted" style="font-size:.8rem;text-align:center;padding:16px;">Sin actividad reciente</div>`;
      return;
    }

    list.innerHTML = '';
    recent.forEach(p => {
      const color = CAT_COLORS[p.category] ?? '#94a3b8';
      const item  = document.createElement('div');
      item.className = 'activity-item';
      item.innerHTML = `
        <span class="activity-dot" style="background:${color};box-shadow:0 0 5px ${color};"></span>
        <div class="activity-info">
          <div class="activity-name">${esc(p.name)}</div>
          <div class="activity-cat">${p.category} · ${fmtDate(p.created_at)}</div>
        </div>
        <div class="activity-amount">$${p.amount.toFixed(2)}</div>
      `;
      list.appendChild(item);
    });
  } catch(e) { /* offline */ }
}

async function loadRightPanelTips() {
  try {
    const data = await api('GET', '/consejos?limit=2');
    const el   = document.getElementById('rp-tips');
    if (!el) return;

    el.innerHTML = '';
    data.tips.forEach(tip => {
      const card = document.createElement('div');
      card.className = `tip-card tip-${tip.color ?? 'blue'}`;
      card.title     = 'Clic para marcar como leído (+5 XP)';
      card.innerHTML = `
        <span class="tip-icon">${tip.icon}</span>
        <div class="tip-body">
          <div class="tip-title">${esc(tip.title)}</div>
          <div class="tip-text">${esc(tip.text)}</div>
        </div>
      `;
      card.addEventListener('click', async () => {
        try {
          await api('POST', '/consejos/leer');
          toast('📚 +5 XP — Consejo leído', 'award');
          loadDashboard();
          loadRightPanelTips();
        } catch(e) { /* silent */ }
      });
      el.appendChild(card);
    });
  } catch(e) { /* offline */ }
}

// ═══════════════════════════════════════════════════════════════
// CONFIG SECTION
// ═══════════════════════════════════════════════════════════════

async function loadConfig() {
  try {
    const [budgetData, profileData, statsData] = await Promise.all([
      api('GET', '/presupuesto'),
      api('GET', '/perfil'),
      api('GET', '/estadisticas'),
    ]);

    const budgetInput = document.getElementById('cfg-budget');
    if (budgetInput && budgetData.monthly_amount > 0)
      budgetInput.value = budgetData.monthly_amount;

    const nameInput   = document.getElementById('cfg-name');
    const avatarInput = document.getElementById('cfg-avatar');
    if (nameInput)   nameInput.value   = profileData.name ?? '';
    if (avatarInput) avatarInput.value = profileData.avatar ?? '';

    // Global stats
    const statsEl = document.getElementById('global-stats');
    if (statsEl) {
      const gt = statsData.grand_total;
      statsEl.innerHTML = `
        <div class="mini-stat"><div class="mini-stat-value" style="color:#4facfe;">${gt.count}</div><div class="mini-stat-label">Total gastos</div></div>
        <div class="mini-stat"><div class="mini-stat-value" style="color:#a855f7;">$${(gt.total??0).toFixed(0)}</div><div class="mini-stat-label">Total gastado</div></div>
        <div class="mini-stat"><div class="mini-stat-value" style="color:#ec4899;">${profileData.xp}</div><div class="mini-stat-label">XP total</div></div>
        <div class="mini-stat"><div class="mini-stat-value" style="color:#22d3ee;">${profileData.level}</div><div class="mini-stat-label">Nivel</div></div>
      `;
    }
  } catch(e) { console.error(e); }
}

async function saveBudget() {
  const input = document.getElementById('cfg-budget');
  const val   = parseFloat(input?.value);
  if (isNaN(val) || val < 0) return toast('Ingresa un monto válido', 'error');
  try {
    await api('POST', '/presupuesto', { amount: val });
    showAlert('cfg-budget-ok', `✅ Presupuesto de $${val.toFixed(2)} guardado.`);
    toast('💰 Presupuesto guardado', 'success');
    loadDashboard();
  } catch(e) { toast('Error al guardar', 'error'); }
}

async function saveProfile() {
  const name   = document.getElementById('cfg-name')?.value.trim();
  const avatar = document.getElementById('cfg-avatar')?.value.trim().toUpperCase().slice(0,2);
  if (!name) return toast('Ingresa tu nombre', 'error');
  try {
    await api('PUT', '/perfil', { name, avatar });
    showAlert('cfg-profile-ok', `✅ Perfil actualizado.`);
    toast('👤 Perfil guardado', 'success');
    loadDashboard();
  } catch(e) { toast('Error al guardar', 'error'); }
}

// ═══════════════════════════════════════════════════════════════
// API HELPER
// ═══════════════════════════════════════════════════════════════

async function api(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',   // send/receive session cookies
  };
  if (body) opts.body = JSON.stringify(body);
  const res  = await fetch(API + path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

// ═══════════════════════════════════════════════════════════════
// TOAST NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════

function toast(msg, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const icons = { success:'✅', error:'❌', info:'ℹ️', award:'🏆' };
  const div   = document.createElement('div');
  div.className = `toast ${type}`;
  div.innerHTML = `<span>${icons[type] ?? 'ℹ️'}</span><span>${msg}</span>`;
  container.appendChild(div);

  setTimeout(() => {
    div.style.opacity = '0';
    div.style.transform = 'translateY(16px)';
    div.style.transition = '.3s ease';
    setTimeout(() => div.remove(), 320);
  }, duration);
}

// ═══════════════════════════════════════════════════════════════
// ALERT HELPERS
// ═══════════════════════════════════════════════════════════════

function showAlert(id, msg) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 4000);
}

function hideAlert(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('show');
}

// ═══════════════════════════════════════════════════════════════
// LOADING STATE FOR BUTTONS
// ═══════════════════════════════════════════════════════════════

function setLoading(prefix, loading) {
  const btn     = document.getElementById(`${prefix}-submit`);
  const spinner = document.getElementById(`${prefix}-spinner`);
  const text    = btn?.querySelector('.btn-text');
  if (!btn) return;
  btn.disabled = loading;
  if (spinner) spinner.classList.toggle('hidden', !loading);
  if (text)    text.textContent = loading ? 'Guardando…' : 'Agregar gasto';
}

// ═══════════════════════════════════════════════════════════════
// UTILS
// ═══════════════════════════════════════════════════════════════

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function fmt(n) {
  return '$' + (n ?? 0).toFixed(2);
}

function fmtDate(str) {
  if (!str) return '';
  try {
    const d = new Date(str.replace(' ', 'T'));
    return d.toLocaleDateString('es', { day:'2-digit', month:'short' });
  } catch { return ''; }
}

function esc(str) {
  const d = document.createElement('div');
  d.textContent = str ?? '';
  return d.innerHTML;
}
