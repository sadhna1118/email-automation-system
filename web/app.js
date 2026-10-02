/**
 * AuraMail Pro — Web Control Center SPA Logic
 */

// State
let currentTab = 'dashboard';
let templatesCache = [];
let contactListsCache = [];
let activePollingTimer = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initComposer();
  initModals();
  initForms();
  initDropzone();
  
  // Load initial data
  loadDashboard();
  loadTemplates();
  loadContactLists();
  loadSettings();
  
  // Start background periodic refresh for live metrics and campaigns
  activePollingTimer = setInterval(() => {
    if (currentTab === 'dashboard') loadDashboard(false);
    if (currentTab === 'campaigns') loadCampaigns();
    if (currentTab === 'inbox') loadInbox();
  }, 5000);
});

// Toast notification helper
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span> <span>${message}</span>`;
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ---------------- Navigation ---------------- //

function initNavigation() {
  const navButtons = document.querySelectorAll('.nav-item');
  navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.getAttribute('data-tab');
      switchTab(tabId);
    });
  });

  document.getElementById('btn-header-quick-send')?.addEventListener('click', () => switchTab('composer'));
  document.getElementById('btn-header-new-campaign')?.addEventListener('click', () => openModal('modal-campaign'));
  document.getElementById('btn-seed-data')?.addEventListener('click', seedDemoData);
}

function switchTab(tabId) {
  currentTab = tabId;
  
  // Update nav active
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
  });
  
  // Update view active
  document.querySelectorAll('.tab-view').forEach(view => {
    view.classList.toggle('active', view.id === `view-${tabId}`);
  });

  // Update header text
  const titles = {
    'dashboard': ['Dashboard Overview', 'Real-time performance analytics and system metrics'],
    'campaigns': ['Bulk Email Campaigns', 'Automate targeted email broadcasts with throttling & live progress'],
    'composer': ['Email Composer', 'Compose, preview, and test-send personalized emails'],
    'templates': ['Template Studio', 'Design, edit, and organize responsive HTML email templates'],
    'contacts': ['Audience & Contact Lists', 'Import contacts via CSV with validation and manage subscriber segments'],
    'inbox': ['Live Inbox & Rule Monitor', 'Inspect incoming emails captured by IMAP listener and rule triggers'],
    'rules': ['Smart Notification Rules', 'Configure automated triggers, alerts, auto-replies, and webhook events'],
    'scheduler': ['Persistent Task Scheduler', 'Automate recurring inbox checks, bulk email sends, and performance digests'],
    'settings': ['System Settings & SMTP Diagnostic', 'Manage credentials, simulation dry-run mode, and test email connections']
  };

  if (titles[tabId]) {
    document.getElementById('page-title').textContent = titles[tabId][0];
    document.getElementById('page-subtitle').textContent = titles[tabId][1];
  }

  // Refresh tab content
  if (tabId === 'dashboard') loadDashboard();
  if (tabId === 'campaigns') loadCampaigns();
  if (tabId === 'templates') loadTemplates();
  if (tabId === 'contacts') loadContacts();
  if (tabId === 'inbox') loadInbox();
  if (tabId === 'rules') loadRules();
  if (tabId === 'scheduler') loadScheduler();
  if (tabId === 'settings') loadSettings();
}

// ---------------- Dashboard ---------------- //

async function loadDashboard(showLoading = true) {
  try {
    const res = await fetch('/api/stats');
    const stats = await res.json();

    document.getElementById('stat-sent').textContent = stats.sent.toLocaleString();
    document.getElementById('stat-delivery-rate').textContent = `${stats.delivery_rate}%`;
    document.getElementById('stat-opened').textContent = stats.opened.toLocaleString();
    document.getElementById('stat-open-rate').textContent = `${stats.open_rate}%`;
    document.getElementById('stat-clicked').textContent = stats.clicked.toLocaleString();
    document.getElementById('stat-click-rate').textContent = `${stats.click_rate}%`;
    document.getElementById('stat-monitored').textContent = stats.monitored.toLocaleString();
    document.getElementById('stat-active-rules').textContent = stats.active_rules;

    document.getElementById('badge-inbox').textContent = stats.monitored;
    document.getElementById('badge-campaigns').textContent = stats.total_campaigns;

    // Simulation badge
    const modeLabel = document.getElementById('system-mode-label');
    const dot = document.getElementById('system-status-dot');
    if (stats.dry_run) {
      modeLabel.textContent = 'Simulation Mode (Safe)';
      modeLabel.style.color = '#60a5fa';
    } else {
      modeLabel.textContent = 'Live Production Mode';
      modeLabel.style.color = '#10b981';
    }

    // Render 7-day canvas chart
    renderDailyChart(stats.daily_stats || []);

    // Load recent activity logs
    loadActivities();
  } catch (err) {
    console.error('Failed to load dashboard stats:', err);
  }
}

async function loadActivities() {
  try {
    const res = await fetch('/api/activities?limit=15');
    const logs = await res.json();
    const container = document.getElementById('activity-list');
    
    if (!logs || logs.length === 0) {
      container.innerHTML = '<div class="empty-state">No recent activity</div>';
      return;
    }

    container.innerHTML = logs.map(l => `
      <div class="activity-item">
        <div>
          <div class="activity-desc">${escapeHtml(l.description)}</div>
          <div class="activity-time">${l.created_at}</div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to load activities:', err);
  }
}

function renderDailyChart(data) {
  const canvas = document.getElementById('dailyChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  
  // High DPI scaling
  const dpr = window.devicePixelRatio || 1;
  canvas.width = canvas.parentElement.clientWidth * dpr;
  canvas.height = 220 * dpr;
  ctx.scale(dpr, dpr);

  const width = canvas.parentElement.clientWidth;
  const height = 220;
  const padding = 35;

  ctx.clearRect(0, 0, width, height);

  // Fill sample dates if data is empty
  let points = data;
  if (!points || points.length === 0) {
    points = [
      { date: 'Mon', sent: 12 },
      { date: 'Tue', sent: 28 },
      { date: 'Wed', sent: 45 },
      { date: 'Thu', sent: 32 },
      { date: 'Fri', sent: 68 },
      { date: 'Sat', sent: 50 },
      { date: 'Sun', sent: 84 }
    ];
  }

  const maxVal = Math.max(...points.map(p => p.sent || 0), 10);
  const stepX = (width - padding * 2) / (points.length - 1 || 1);

  // Draw grid lines
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = padding + (height - padding * 2) * (i / 4);
    ctx.beginPath();
    ctx.moveTo(padding, y);
    ctx.lineTo(width - padding, y);
    ctx.stroke();
  }

  // Draw gradient area
  const gradient = ctx.createLinearGradient(0, padding, 0, height - padding);
  gradient.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
  gradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

  ctx.beginPath();
  points.forEach((p, idx) => {
    const x = padding + idx * stepX;
    const y = height - padding - ((p.sent || 0) / maxVal) * (height - padding * 2);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });

  ctx.lineTo(padding + (points.length - 1) * stepX, height - padding);
  ctx.lineTo(padding, height - padding);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();

  // Draw line
  ctx.strokeStyle = '#6366f1';
  ctx.lineWidth = 3;
  ctx.beginPath();
  points.forEach((p, idx) => {
    const x = padding + idx * stepX;
    const y = height - padding - ((p.sent || 0) / maxVal) * (height - padding * 2);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Draw data dots & labels
  ctx.fillStyle = '#94a3b8';
  ctx.font = '11px Inter, sans-serif';
  ctx.textAlign = 'center';

  points.forEach((p, idx) => {
    const x = padding + idx * stepX;
    const y = height - padding - ((p.sent || 0) / maxVal) * (height - padding * 2);

    // Dot
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Date label
    ctx.fillStyle = '#94a3b8';
    const label = p.date ? p.date.split('-').slice(1).join('/') : `D${idx+1}`;
    ctx.fillText(label, x, height - 12);
  });
}

// ---------------- Campaigns ---------------- //

async function loadCampaigns() {
  try {
    const res = await fetch('/api/campaigns');
    const campaigns = await res.json();
    const container = document.getElementById('campaigns-container');

    if (!campaigns || campaigns.length === 0) {
      container.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <h3>No campaigns found</h3>
          <p>Launch your first automated campaign with a selected template and contact list.</p>
          <button class="btn btn-glow" onclick="openModal('modal-campaign')" style="margin-top: 14px;">Launch First Campaign</button>
        </div>
      `;
      return;
    }

    container.innerHTML = campaigns.map(c => {
      const total = c.total_recipients || 0;
      const sent = c.sent_count || 0;
      const failed = c.failed_count || 0;
      const percent = total > 0 ? Math.round((sent / total) * 100) : 0;
      const statusClass = `status-${c.status.toLowerCase()}`;

      return `
        <div class="campaign-card" id="camp-card-${c.id}">
          <div class="campaign-top">
            <div>
              <div class="campaign-name">${escapeHtml(c.name)}</div>
              <div class="campaign-meta">Template: ${escapeHtml(c.template_name || 'Custom')} &bull; List: ${escapeHtml(c.list_name || 'Audience')}</div>
            </div>
            <span class="badge-status ${statusClass}">${c.status}</span>
          </div>

          <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: ${percent}%;"></div>
          </div>

          <div class="campaign-stats-row">
            <span>Progress: <strong>${sent} / ${total}</strong> (${percent}%)</span>
            <span>Failed: <strong style="color: ${failed > 0 ? '#ef4444' : '#94a3b8'};">${failed}</strong></span>
          </div>

          <div class="campaign-card-actions">
            ${c.status === 'draft' || c.status === 'scheduled' ? `
              <button class="btn btn-sm btn-primary" onclick="startCampaign(${c.id})">Start Campaign</button>
            ` : ''}
            ${c.status === 'running' ? `
              <button class="btn btn-sm btn-secondary" onclick="pauseCampaign(${c.id})">Pause</button>
              <button class="btn btn-sm btn-secondary" onclick="cancelCampaign(${c.id})" style="color:#ef4444;">Cancel</button>
            ` : ''}
            ${c.status === 'paused' ? `
              <button class="btn btn-sm btn-primary" onclick="resumeCampaign(${c.id})">Resume</button>
              <button class="btn btn-sm btn-secondary" onclick="cancelCampaign(${c.id})" style="color:#ef4444;">Cancel</button>
            ` : ''}
            ${c.status === 'completed' ? `
              <span style="font-size: 12px; color: #10b981; font-weight: 600;">✓ Completed at ${c.completed_at || ''}</span>
            ` : ''}
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error('Failed to load campaigns:', err);
  }
}

async function startCampaign(id) {
  try {
    const res = await fetch(`/api/campaigns/${id}/start`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(`Campaign #${id} started successfully!`);
      loadCampaigns();
    } else {
      showToast(data.detail || data.message, 'error');
    }
  } catch (err) {
    showToast('Failed to start campaign', 'error');
  }
}

async function pauseCampaign(id) {
  await fetch(`/api/campaigns/${id}/pause`, { method: 'POST' });
  showToast('Campaign paused');
  loadCampaigns();
}

async function resumeCampaign(id) {
  await fetch(`/api/campaigns/${id}/resume`, { method: 'POST' });
  showToast('Campaign resumed');
  loadCampaigns();
}

async function cancelCampaign(id) {
  if (confirm('Are you sure you want to cancel this campaign?')) {
    await fetch(`/api/campaigns/${id}/cancel`, { method: 'POST' });
    showToast('Campaign cancelled');
    loadCampaigns();
  }
}

// ---------------- Composer & Live Preview ---------------- //

function initComposer() {
  const subjectInput = document.getElementById('composer-subject');
  const bodyInput = document.getElementById('composer-body');
  const templateSelect = document.getElementById('composer-template-select');
  const spamBtn = document.getElementById('btn-check-spam-composer');
  const viewportDesktop = document.getElementById('btn-viewport-desktop');
  const viewportMobile = document.getElementById('btn-viewport-mobile');
  const frameWrapper = document.getElementById('preview-frame-wrapper');

  // Debounced live preview update
  let timer = null;
  const updatePreview = () => {
    clearTimeout(timer);
    timer = setTimeout(renderLivePreview, 250);
  };

  subjectInput?.addEventListener('input', updatePreview);
  bodyInput?.addEventListener('input', updatePreview);

  // Template select change
  templateSelect?.addEventListener('change', (e) => {
    const tmplId = e.target.value;
    if (!tmplId) return;
    const found = templatesCache.find(t => t.id == tmplId);
    if (found) {
      subjectInput.value = found.subject_template;
      bodyInput.value = found.body_html;
      updatePreview();
    }
  });

  // Spam check button
  spamBtn?.addEventListener('click', checkSpamScore);

  // Viewport switcher
  viewportDesktop?.addEventListener('click', () => {
    viewportDesktop.classList.add('active');
    viewportMobile.classList.remove('active');
    frameWrapper.classList.remove('mobile');
  });

  viewportMobile?.addEventListener('click', () => {
    viewportMobile.classList.add('active');
    viewportDesktop.classList.remove('active');
    frameWrapper.classList.add('mobile');
  });

  // Send single email form
  document.getElementById('composer-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const to = document.getElementById('composer-to').value;
    const cc = document.getElementById('composer-cc').value;
    const bcc = document.getElementById('composer-bcc').value;
    const subject = subjectInput.value;
    const body = bodyInput.value;
    const isHtml = document.getElementById('composer-is-html').checked;

    try {
      const res = await fetch('/api/send-single', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to_email: to,
          subject: subject,
          body: body,
          html: isHtml,
          cc: cc || null,
          bcc: bcc || null
        })
      });

      const data = await res.json();
      if (res.ok) {
        showToast(data.message);
        document.getElementById('composer-form').reset();
        updatePreview();
      } else {
        showToast(data.detail || 'Failed to send email', 'error');
      }
    } catch (err) {
      showToast('Network error while sending email', 'error');
    }
  });
}

function insertVariable(varName) {
  const bodyInput = document.getElementById('composer-body');
  if (!bodyInput) return;
  const tag = `{${varName}}`;
  const start = bodyInput.selectionStart;
  const end = bodyInput.selectionEnd;
  bodyInput.value = bodyInput.value.substring(0, start) + tag + bodyInput.value.substring(end);
  bodyInput.focus();
  bodyInput.selectionStart = bodyInput.selectionEnd = start + tag.length;
  renderLivePreview();
}

async function renderLivePreview() {
  const subject = document.getElementById('composer-subject')?.value || '(No Subject)';
  const body = document.getElementById('composer-body')?.value || '<p style="color:#64748b;font-family:sans-serif;padding:20px;">Start typing email content to see live preview...</p>';
  
  document.getElementById('preview-subject-bar').textContent = `Subject: ${subject}`;

  try {
    const res = await fetch('/api/templates/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject_template: subject, body_html: body })
    });
    const data = await res.json();
    
    const iframe = document.getElementById('preview-iframe');
    if (iframe) {
      const doc = iframe.contentDocument || iframe.contentWindow.document;
      doc.open();
      doc.write(data.html);
      doc.close();
    }
  } catch (err) {
    console.error('Preview error:', err);
  }
}

async function checkSpamScore() {
  const subject = document.getElementById('composer-subject')?.value || '';
  const body = document.getElementById('composer-body')?.value || '';

  try {
    const res = await fetch('/api/templates/spam-check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject, body })
    });
    const data = await res.json();

    const box = document.getElementById('spam-score-box');
    const badge = document.getElementById('spam-score-badge');
    const reasons = document.getElementById('spam-reasons-list');

    box.style.display = 'block';
    badge.className = `spam-badge ${data.status}`;
    badge.textContent = `${data.score}/100 — ${data.verdict}`;

    let html = '';
    if (data.reasons.length > 0) {
      html += `<strong>Observations:</strong><ul>${data.reasons.map(r => `<li>${r}</li>`).join('')}</ul>`;
    }
    if (data.recommendations.length > 0) {
      html += `<strong>Recommendations:</strong><ul>${data.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>`;
    }
    if (data.reasons.length === 0 && data.recommendations.length === 0) {
      html = '<div style="color:#10b981;">✓ Excellent email format! High deliverability expected.</div>';
    }

    reasons.innerHTML = html;
  } catch (err) {
    showToast('Failed to analyze spam score', 'error');
  }
}

// ---------------- Templates Studio ---------------- //

async function loadTemplates() {
  try {
    const res = await fetch('/api/templates');
    templatesCache = await res.json();
    
    // Update select dropdowns
    const compSelect = document.getElementById('composer-template-select');
    const campSelect = document.getElementById('campaign-template-select');
    
    if (compSelect) {
      compSelect.innerHTML = '<option value="">-- Load a Template --</option>' + 
        templatesCache.map(t => `<option value="${t.id}">${escapeHtml(t.name)}</option>`).join('');
    }
    if (campSelect) {
      campSelect.innerHTML = templatesCache.map(t => `<option value="${t.id}">${escapeHtml(t.name)}</option>`).join('');
    }

    // Render cards
    const container = document.getElementById('templates-container');
    if (!container) return;

    if (templatesCache.length === 0) {
      container.innerHTML = '<div class="empty-state">No templates found</div>';
      return;
    }

    container.innerHTML = templatesCache.map(t => `
      <div class="template-card">
        <div class="template-badge">${t.category || 'General'}</div>
        <h3>${escapeHtml(t.name)}</h3>
        <div class="template-subject-preview">Subj: ${escapeHtml(t.subject_template)}</div>
        <div class="template-actions">
          <button class="btn btn-sm btn-primary" onclick="useTemplateInComposer(${t.id})">Use in Composer</button>
          <button class="btn btn-sm btn-secondary" onclick="deleteTemplate(${t.id})">Delete</button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to load templates:', err);
  }
}

function useTemplateInComposer(id) {
  const found = templatesCache.find(t => t.id == id);
  if (found) {
    switchTab('composer');
    document.getElementById('composer-subject').value = found.subject_template;
    document.getElementById('composer-body').value = found.body_html;
    renderLivePreview();
  }
}

async function deleteTemplate(id) {
  if (confirm('Delete this template?')) {
    await fetch(`/api/templates/${id}`, { method: 'DELETE' });
    showToast('Template deleted');
    loadTemplates();
  }
}

// ---------------- Contacts & Audience ---------------- //

async function loadContacts(search = '') {
  try {
    const res = await fetch(`/api/contacts?search=${encodeURIComponent(search)}`);
    const data = await res.json();
    const tbody = document.getElementById('contacts-tbody');
    const subTitle = document.getElementById('contacts-table-sub');

    if (subTitle) subTitle.textContent = `${data.total} total contacts`;

    if (!data.contacts || data.contacts.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty-cell">No contacts match the criteria</td></tr>';
      return;
    }

    tbody.innerHTML = data.contacts.map(c => `
      <tr>
        <td><strong>${escapeHtml(c.email)}</strong></td>
        <td>${escapeHtml(c.name || '—')}</td>
        <td>${escapeHtml(c.company || '—')}</td>
        <td><span class="badge-status status-${c.status === 'active' ? 'running' : 'cancelled'}">${c.status}</span></td>
        <td>${c.created_at || '—'}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Failed to load contacts:', err);
  }
}

async function loadContactLists() {
  try {
    const res = await fetch('/api/contact-lists');
    contactListsCache = await res.json();
    const container = document.getElementById('contact-lists-container');
    const campListSelect = document.getElementById('campaign-list-select');

    if (campListSelect) {
      campListSelect.innerHTML = contactListsCache.map(l => `<option value="${l.id}">${escapeHtml(l.name)} (${l.member_count} subscribers)</option>`).join('');
    }

    if (!container) return;
    if (contactListsCache.length === 0) {
      container.innerHTML = '<div class="empty-state">No lists created yet</div>';
      return;
    }

    container.innerHTML = `
      <div class="list-item active" onclick="loadContacts()">
        <span class="list-item-name">All Subscribers</span>
      </div>
      ${contactListsCache.map(l => `
        <div class="list-item" onclick="filterByList(${l.id})">
          <span class="list-item-name">${escapeHtml(l.name)}</span>
          <span class="list-item-count">${l.member_count}</span>
        </div>
      `).join('')}
    `;
  } catch (err) {
    console.error('Failed to load contact lists:', err);
  }
}

function filterByList(listId) {
  // Filter contacts by list
  loadContacts();
}

// ---------------- Live Inbox & Monitor ---------------- //

async function loadInbox() {
  try {
    const res = await fetch('/api/inbox');
    const emails = await res.json();
    const list = document.getElementById('inbox-messages-list');
    const badge = document.getElementById('inbox-count-badge');

    if (badge) badge.textContent = emails.length;

    if (!emails || emails.length === 0) {
      list.innerHTML = '<div class="empty-state">No incoming monitored messages yet.</div>';
      return;
    }

    list.innerHTML = emails.map((m, idx) => `
      <div class="inbox-msg-item ${idx === 0 ? 'active' : ''}" onclick="selectInboxMessage(${m.id})">
        <div class="inbox-msg-sender">${escapeHtml(m.sender)}</div>
        <div class="inbox-msg-subject">${escapeHtml(m.subject)}</div>
        <div class="inbox-msg-preview">${escapeHtml(m.body_preview || '')}</div>
      </div>
    `).join('');

    if (emails.length > 0) {
      renderInboxDetail(emails[0]);
    }
  } catch (err) {
    console.error('Failed to load inbox:', err);
  }
}

async function selectInboxMessage(id) {
  try {
    const res = await fetch('/api/inbox');
    const emails = await res.json();
    const found = emails.find(e => e.id == id);
    if (found) {
      renderInboxDetail(found);
    }
  } catch (err) {}
}

function renderInboxDetail(email) {
  const panel = document.getElementById('inbox-detail-panel');
  if (!panel) return;

  panel.innerHTML = `
    <div class="inbox-detail-header">
      <div class="inbox-detail-subject">${escapeHtml(email.subject)}</div>
      <div class="inbox-detail-meta">
        From: <strong>${escapeHtml(email.sender)}</strong> &bull; Received: ${email.received_at}
      </div>
    </div>
    <div class="inbox-detail-body">
      ${email.body_html || `<pre style="white-space:pre-wrap;font-family:inherit;">${escapeHtml(email.body_text || email.body_preview || '')}</pre>`}
    </div>
  `;
}

// ---------------- Smart Rules ---------------- //

async function loadRules() {
  try {
    const res = await fetch('/api/rules');
    const rules = await res.json();
    const container = document.getElementById('rules-container');

    if (!rules || rules.length === 0) {
      container.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;">No smart rules configured yet.</div>';
      return;
    }

    container.innerHTML = rules.map(r => `
      <div class="glass-panel">
        <div class="panel-header">
          <div>
            <h3>${escapeHtml(r.rule_name)}</h3>
            <p>Action: <strong>${r.action_type}</strong> &bull; Triggers: ${r.trigger_count || 0}</p>
          </div>
          <span class="badge-status ${r.enabled ? 'status-running' : 'status-draft'}">${r.enabled ? 'Active' : 'Disabled'}</span>
        </div>
        <div style="font-size: 13px; color: #94a3b8; margin-bottom: 16px;">
          ${r.sender_filter ? `<div>Sender contains: <code>${escapeHtml(r.sender_filter)}</code></div>` : ''}
          ${r.subject_filter ? `<div>Subject contains: <code>${escapeHtml(r.subject_filter)}</code></div>` : ''}
          ${r.keyword_filter ? `<div>Keywords: <code>${escapeHtml(r.keyword_filter)}</code></div>` : ''}
        </div>
        <div style="display:flex; gap: 8px;">
          <button class="btn btn-sm btn-secondary" onclick="toggleRule(${r.id})">${r.enabled ? 'Disable' : 'Enable'}</button>
          <button class="btn btn-sm btn-secondary" onclick="deleteRule(${r.id})" style="color:#ef4444;">Delete</button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to load rules:', err);
  }
}

async function toggleRule(id) {
  await fetch(`/api/rules/${id}/toggle`, { method: 'POST' });
  loadRules();
}

async function deleteRule(id) {
  if (confirm('Delete rule?')) {
    await fetch(`/api/rules/${id}`, { method: 'DELETE' });
    loadRules();
  }
}

// ---------------- Scheduler ---------------- //

async function loadScheduler() {
  try {
    const res = await fetch('/api/scheduler');
    const tasks = await res.json();
    const tbody = document.getElementById('scheduler-tbody');

    if (!tasks || tasks.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty-cell">No scheduled tasks</td></tr>';
      return;
    }

    tbody.innerHTML = tasks.map(t => `
      <tr>
        <td><strong>${escapeHtml(t.task_name)}</strong></td>
        <td>${t.task_type}</td>
        <td><code>${t.schedule_expr}</code></td>
        <td><span class="badge-status ${t.enabled ? 'status-running' : 'status-draft'}">${t.enabled ? 'Active' : 'Paused'}</span></td>
        <td>
          <button class="btn btn-sm btn-secondary" onclick="toggleSchedule(${t.id})">${t.enabled ? 'Pause' : 'Activate'}</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Failed to load scheduler:', err);
  }
}

async function toggleSchedule(id) {
  await fetch(`/api/scheduler/${id}/toggle`, { method: 'POST' });
  loadScheduler();
}

// ---------------- Settings & Diagnostics ---------------- //

async function loadSettings() {
  try {
    const res = await fetch('/api/settings');
    const cfg = await res.json();

    document.getElementById('cfg-smtp-server').value = cfg.smtp_server || '';
    document.getElementById('cfg-smtp-port').value = cfg.smtp_port || 587;
    document.getElementById('cfg-smtp-tls').checked = cfg.smtp_use_tls !== false;
    document.getElementById('cfg-smtp-ssl').checked = !!cfg.smtp_use_ssl;
    document.getElementById('cfg-email-address').value = cfg.email_address || '';
    document.getElementById('cfg-sender-name').value = cfg.sender_name || '';
    document.getElementById('cfg-imap-server').value = cfg.imap_server || '';
    document.getElementById('cfg-imap-port').value = cfg.imap_port || 993;
    document.getElementById('cfg-dry-run').checked = cfg.dry_run !== false;
    document.getElementById('cfg-tracking-enabled').checked = cfg.tracking_enabled !== false;
    document.getElementById('cfg-rate-limit').value = cfg.rate_limit_delay || 1.0;
    document.getElementById('cfg-batch-size').value = cfg.batch_size || 50;
    document.getElementById('cfg-notification-email').value = cfg.notification_email || '';
    document.getElementById('cfg-webhook-url').value = cfg.webhook_url || '';
  } catch (err) {
    console.error('Failed to load settings:', err);
  }
}

// ---------------- Modals & Forms ---------------- //

function initModals() {
  document.getElementById('btn-create-campaign-modal')?.addEventListener('click', () => openModal('modal-campaign'));
  document.getElementById('btn-create-template-modal')?.addEventListener('click', () => openModal('modal-template'));
  document.getElementById('btn-import-csv-modal')?.addEventListener('click', () => openModal('modal-csv'));
  document.getElementById('btn-create-rule-modal')?.addEventListener('click', () => openModal('modal-rule'));
  document.getElementById('btn-simulate-email-modal')?.addEventListener('click', () => openModal('modal-simulate'));
  document.getElementById('btn-check-inbox-now')?.addEventListener('click', async () => {
    const res = await fetch('/api/inbox/check-now', { method: 'POST' });
    const d = await res.json();
    showToast(d.message);
    loadInbox();
  });

  // SMTP Test Button
  document.getElementById('btn-test-smtp')?.addEventListener('click', async () => {
    showToast('Testing SMTP connection...', 'info');
    const res = await fetch('/api/settings/test-smtp', { method: 'POST' });
    const d = await res.json();
    showToast(d.message, d.success ? 'success' : 'error');
  });
}

function openModal(id) {
  document.getElementById(id)?.classList.add('active');
}

function closeModals() {
  document.querySelectorAll('.modal-backdrop').forEach(m => m.classList.remove('active'));
}

function initForms() {
  // New Campaign
  document.getElementById('form-new-campaign')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('campaign-name-input').value;
    const template_id = parseInt(document.getElementById('campaign-template-select').value);
    const contact_list_id = parseInt(document.getElementById('campaign-list-select').value);
    const delay_seconds = parseFloat(document.getElementById('campaign-delay-input').value);
    const batch_size = parseInt(document.getElementById('campaign-batch-input').value);

    const res = await fetch('/api/campaigns', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, template_id, contact_list_id, delay_seconds, batch_size })
    });
    const d = await res.json();
    if (d.success) {
      showToast('Campaign created! Starting...');
      closeModals();
      await startCampaign(d.campaign_id);
    }
  });

  // New Template
  document.getElementById('form-new-template')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('tmpl-name-input').value;
    const category = document.getElementById('tmpl-category-input').value;
    const subject_template = document.getElementById('tmpl-subject-input').value;
    const body_html = document.getElementById('tmpl-html-input').value;

    const res = await fetch('/api/templates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, category, subject_template, body_html })
    });
    const d = await res.json();
    if (d.success) {
      showToast('Template saved successfully');
      closeModals();
      loadTemplates();
    }
  });

  // New Rule
  document.getElementById('form-new-rule')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const rule_name = document.getElementById('rule-name-input').value;
    const sender_filter = document.getElementById('rule-sender-input').value || null;
    const subject_filter = document.getElementById('rule-subject-input').value || null;
    const keyword_filter = document.getElementById('rule-keyword-input').value || null;
    const condition_logic = document.getElementById('rule-logic-select').value;
    const action_type = document.getElementById('rule-action-select').value;

    const res = await fetch('/api/rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rule_name, sender_filter, subject_filter, keyword_filter, condition_logic, action_type })
    });
    const d = await res.json();
    if (d.success) {
      showToast('Smart Rule saved');
      closeModals();
      loadRules();
    }
  });

  // Simulate Email
  document.getElementById('form-simulate-email')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const sender = document.getElementById('sim-sender-input').value;
    const subject = document.getElementById('sim-subject-input').value;
    const body = document.getElementById('sim-body-input').value;

    const res = await fetch('/api/inbox/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sender, subject, body })
    });
    const d = await res.json();
    if (d.success) {
      showToast('Simulated email processed!');
      closeModals();
      loadInbox();
      loadDashboard();
    }
  });

  // Settings Save
  document.getElementById('settings-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
      smtp_server: document.getElementById('cfg-smtp-server').value,
      smtp_port: parseInt(document.getElementById('cfg-smtp-port').value),
      smtp_use_tls: document.getElementById('cfg-smtp-tls').checked,
      smtp_use_ssl: document.getElementById('cfg-smtp-ssl').checked,
      imap_server: document.getElementById('cfg-imap-server').value,
      imap_port: parseInt(document.getElementById('cfg-imap-port').value),
      imap_use_ssl: true,
      email_address: document.getElementById('cfg-email-address').value,
      sender_name: document.getElementById('cfg-sender-name').value,
      notification_email: document.getElementById('cfg-notification-email').value,
      dry_run: document.getElementById('cfg-dry-run').checked,
      rate_limit_delay: parseFloat(document.getElementById('cfg-rate-limit').value),
      batch_size: parseInt(document.getElementById('cfg-batch-size').value),
      tracking_enabled: document.getElementById('cfg-tracking-enabled').checked,
      webhook_url: document.getElementById('cfg-webhook-url').value
    };

    const pwd = document.getElementById('cfg-email-password').value;
    if (pwd) data.email_password = pwd;

    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    const d = await res.json();
    showToast(d.message);
    loadDashboard();
  });
}

function initDropzone() {
  const dropzone = document.getElementById('csv-dropzone');
  const fileInput = document.getElementById('csv-file-input');
  const dropText = document.getElementById('dropzone-text');

  dropzone?.addEventListener('click', () => fileInput.click());
  
  fileInput?.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      dropText.textContent = `📄 Selected: ${fileInput.files[0].name} (${Math.round(fileInput.files[0].size / 1024)} KB)`;
    }
  });

  document.getElementById('form-import-csv')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!fileInput.files.length) {
      showToast('Please choose a CSV file', 'error');
      return;
    }

    const listName = document.getElementById('csv-list-name').value;
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('list_name', listName);

    try {
      const res = await fetch('/api/contacts/import-csv', {
        method: 'POST',
        body: formData
      });
      const d = await res.json();
      if (d.success) {
        showToast(`Successfully imported ${d.valid_count} contacts!`);
        closeModals();
        loadContactLists();
        loadContacts();
      } else {
        showToast(d.detail || 'Failed to import CSV', 'error');
      }
    } catch (err) {
      showToast('CSV upload error', 'error');
    }
  });
}

// ---------------- Demo Seeder ---------------- //

async function seedDemoData() {
  try {
    showToast('Generating enterprise demo contacts & campaign...', 'info');
    
    // 1. Create Demo List
    const listRes = await fetch('/api/contact-lists', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Enterprise Beta Users', description: 'Sample audience for platform walkthrough' })
    });
    const listData = await listRes.json();
    const listId = listData.list_id;

    // 2. Add Contacts
    const demoContacts = [
      { email: 'sarah.connor@acmetech.io', name: 'Sarah Connor', company: 'Acme Technologies' },
      { email: 'david.beck@novacorp.com', name: 'David Beck', company: 'Nova Corp' },
      { email: 'elena.rostova@quantumscale.ai', name: 'Elena Rostova', company: 'QuantumScale' },
      { email: 'marcus.vance@apexcloud.net', name: 'Marcus Vance', company: 'Apex Cloud' },
      { email: 'rachel.adams@globalprime.org', name: 'Rachel Adams', company: 'GlobalPrime' }
    ];

    for (const c of demoContacts) {
      await fetch('/api/contacts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...c, list_id: listId })
      });
    }

    // 3. Trigger a couple simulated inbox events
    await fetch('/api/inbox/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sender: 'security@partner.com',
        subject: 'Urgent: API rate limit increase request',
        body: 'Hello team, we are hitting throughput limits and need immediate escalation.'
      })
    });

    // 4. Create and launch demo campaign
    if (templatesCache.length > 0 && listId) {
      const campRes = await fetch('/api/campaigns', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'Q3 Product Announcement Broadcast',
          template_id: templatesCache[0].id,
          contact_list_id: listId,
          delay_seconds: 0.5,
          batch_size: 50
        })
      });
      const campData = await campRes.json();
      if (campData.success) {
        await startCampaign(campData.campaign_id);
      }
    }

    showToast('Demo data seeded & sample campaign started!');
    loadDashboard();
    loadContactLists();
    loadCampaigns();
    loadInbox();
  } catch (err) {
    showToast('Failed to seed demo data', 'error');
  }
}

// Utility
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
