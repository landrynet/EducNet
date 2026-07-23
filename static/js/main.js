/* ══════════════════════════════════════════════════════
   EduManager — Main JavaScript
   ══════════════════════════════════════════════════════ */

'use strict';

// ── Sidebar Toggle ───────────────────────────────────
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const mainContent = document.getElementById('main-content');

if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('show');
    // Desktop: collapse to icon-only width
    if (window.innerWidth > 992) {
      if (sidebar.style.width === 'var(--sidebar-collapsed-width)' || sidebar.style.width === '70px') {
        sidebar.style.width = '';
        mainContent.style.marginLeft = '';
      } else {
        sidebar.style.width = '70px';
        mainContent.style.marginLeft = '70px';
      }
    }
  });

  // Close sidebar on outside click (mobile)
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 992 &&
        !sidebar.contains(e.target) &&
        !sidebarToggle.contains(e.target)) {
      sidebar.classList.remove('show');
    }
  });
}

// ── Auto-dismiss alerts ───────────────────────────────
document.querySelectorAll('.alert:not(.alert-static)').forEach(alert => {
  setTimeout(() => {
    const bsAlert = new bootstrap.Alert(alert);
    if (bsAlert) bsAlert.close();
  }, 6000);
});

// ── Active sidebar link highlighting ────────────────
const currentPath = window.location.pathname;
document.querySelectorAll('.sidebar-link').forEach(link => {
  const href = link.getAttribute('href');
  if (href && href !== '/' && currentPath.startsWith(href)) {
    link.classList.add('active');
  } else if (href === '/' && currentPath === '/') {
    link.classList.add('active');
  }
});

// ── Confirm actions ───────────────────────────────────
document.querySelectorAll('[data-confirm]').forEach(el => {
  el.addEventListener('click', (e) => {
    if (!confirm(el.dataset.confirm)) {
      e.preventDefault();
    }
  });
});

// ── Table row clickable ──────────────────────────────
document.querySelectorAll('tr[data-href]').forEach(row => {
  row.style.cursor = 'pointer';
  row.addEventListener('click', () => {
    window.location.href = row.dataset.href;
  });
});

// ── Bootstrap tooltips ───────────────────────────────
const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
tooltips.forEach(el => new bootstrap.Tooltip(el));

// ── Form loading state ───────────────────────────────
// Skip forms inside Bootstrap modals — they manage their own loading state
document.querySelectorAll('form').forEach(form => {
  if (form.closest('.modal')) return;
  form.addEventListener('submit', () => {
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Traitement...';
      setTimeout(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }, 10000);
    }
  });
});

console.log('EduManager v1.0 — Initialisé');
