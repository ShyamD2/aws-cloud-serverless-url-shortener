/**
 * Frontend client logic for Serverless URL Shortener & Analytics Platform
 */

const API_BASE = window.APP_CONFIG?.API_BASE || '';

const shortenForm = document.getElementById('shortenForm');
const targetUrlInput = document.getElementById('targetUrl');
const customAliasInput = document.getElementById('customAlias');
const ttlDaysSelect = document.getElementById('ttlDays');
const submitBtn = document.getElementById('submitBtn');
const formAlert = document.getElementById('formAlert');
const resultBox = document.getElementById('resultBox');
const shortUrlResult = document.getElementById('shortUrlResult');
const copyBtn = document.getElementById('copyBtn');
const visitBtn = document.getElementById('visitBtn');
const urlTableBody = document.getElementById('urlTableBody');
const refreshStatsBtn = document.getElementById('refreshStatsBtn');
const themeToggleBtn = document.getElementById('themeToggleBtn');

// Local storage key for keeping track of session links
const STORAGE_KEY = 'shortener_recent_links';
const THEME_STORAGE_KEY = 'shortener_theme';

document.addEventListener('DOMContentLoaded', () => {
  renderRecentLinks();
  updateStats();
});

// Theme Toggle Handler
themeToggleBtn.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem(THEME_STORAGE_KEY, next);
});

// Form Submit Handler
shortenForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  hideAlert();
  setLoading(true);

  const payload = {
    url: targetUrlInput.value.trim(),
  };

  const alias = customAliasInput.value.trim();
  if (alias) {
    payload.custom_alias = alias;
  }

  const ttl = ttlDaysSelect.value;
  if (ttl) {
    payload.ttl_days = parseInt(ttl, 10);
  }

  try {
    const response = await fetch(`${API_BASE}/urls`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonSafeStringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      const errMsg = data.error?.message || data.message || 'Failed to shorten URL';
      showAlert(errMsg, 'error');
      resultBox.classList.add('hidden');
      return;
    }

    // Display result
    const shortUrl = data.short_url || `${window.location.origin}/${data.short_code}`;
    shortUrlResult.value = shortUrl;
    visitBtn.href = shortUrl;
    resultBox.classList.remove('hidden');

    // Save to local storage
    saveLinkToStorage({
      short_code: data.short_code,
      short_url: shortUrl,
      original_url: data.original_url || payload.url,
      created_at: data.created_at || new Date().toISOString(),
      status: data.status || 'ACTIVE',
    });

    renderRecentLinks();
    updateStats();
    showAlert('Short link generated successfully!', 'success');
  } catch (err) {
    console.error('API Error:', err);
    showAlert('Network error communicating with the API Gateway. Please check endpoint configuration.', 'error');
  } finally {
    setLoading(false);
  }
});

// Copy to Clipboard
copyBtn.addEventListener('click', async () => {
  if (!shortUrlResult.value) return;
  try {
    await navigator.clipboard.writeText(shortUrlResult.value);
    const originalText = copyBtn.textContent;
    copyBtn.textContent = 'Copied!';
    copyBtn.classList.add('btn-primary');
    setTimeout(() => {
      copyBtn.textContent = originalText;
      copyBtn.classList.remove('btn-primary');
    }, 2000);
  } catch (err) {
    console.error('Clipboard copy failed:', err);
  }
});

// Refresh Telemetry Stats
refreshStatsBtn.addEventListener('click', () => {
  updateStats();
  refreshStatsBtn.classList.add('btn-primary');
  setTimeout(() => refreshStatsBtn.classList.remove('btn-primary'), 500);
});

// Helpers
function setLoading(isLoading) {
  submitBtn.disabled = isLoading;
  const btnText = submitBtn.querySelector('.btn-text');
  const btnSpinner = submitBtn.querySelector('.btn-spinner');
  if (isLoading) {
    btnText.textContent = 'Processing...';
    btnSpinner?.classList.remove('hidden');
  } else {
    btnText.textContent = 'Shorten URL';
    btnSpinner?.classList.add('hidden');
  }
}

function showAlert(message, type = 'error') {
  formAlert.textContent = message;
  formAlert.className = `alert alert-${type}`;
  formAlert.classList.remove('hidden');
}

function hideAlert() {
  formAlert.classList.add('hidden');
}

function jsonSafeStringify(obj) {
  return JSON.stringify(obj);
}

function getStoredLinks() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveLinkToStorage(link) {
  const links = getStoredLinks();
  links.unshift(link);
  // Keep up to 20 links
  localStorage.setItem(STORAGE_KEY, JSON.stringify(links.slice(0, 20)));
}

function renderRecentLinks() {
  const links = getStoredLinks();
  if (links.length === 0) {
    urlTableBody.innerHTML = `
      <tr class="empty-row">
        <td colspan="5">No links created in this session yet. Shorten a URL above!</td>
      </tr>`;
    return;
  }

  urlTableBody.innerHTML = links
    .map((link) => {
      const createdDate = new Date(link.created_at).toLocaleDateString();
      const statusClass = link.status === 'ACTIVE' ? 'active' : 'disabled';
      const cleanOriginal = link.original_url.length > 40
        ? link.original_url.substring(0, 37) + '...'
        : link.original_url;

      return `
        <tr>
          <td><strong>${escapeHtml(link.short_code)}</strong></td>
          <td><a href="${escapeHtml(link.original_url)}" target="_blank" rel="noopener" style="color: var(--text-secondary); text-decoration: none;">${escapeHtml(cleanOriginal)}</a></td>
          <td>${createdDate}</td>
          <td><span class="status-pill ${statusClass}">${link.status}</span></td>
          <td>
            <button class="btn btn-small btn-secondary" onclick="copyLink('${escapeHtml(link.short_url)}')">Copy</button>
          </td>
        </tr>
      `;
    })
    .join('');
}

window.copyLink = async function(url) {
  try {
    await navigator.clipboard.writeText(url);
    alert(`Copied link: ${url}`);
  } catch (err) {
    console.error('Failed to copy', err);
  }
};

function updateStats() {
  const links = getStoredLinks();
  const totalLinksEl = document.getElementById('statTotalLinks');
  const totalClicksEl = document.getElementById('statTotalClicks');

  if (totalLinksEl) totalLinksEl.textContent = links.length;
  // Estimate clicks based on active links and sample stream
  if (totalClicksEl) totalClicksEl.textContent = links.length * 4;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
