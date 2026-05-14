/* ============================================================
   ModaAtende — main.js
   Dark mode · Sidebar toggle · Validações · Contadores
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

    /* ── DARK MODE ─────────────────────────────────────── */
    const html        = document.documentElement;
    const darkBtn     = document.getElementById('darkModeToggle');
    const darkIcon    = darkBtn?.querySelector('i');

    const applyTheme = (theme) => {
        html.setAttribute('data-theme', theme);
        if (theme === 'dark') {
            html.classList.add('dark');
        } else {
            html.classList.remove('dark');
        }
        if (darkIcon) {
            darkIcon.className = theme === 'dark'
                ? 'bi bi-sun-fill'
                : 'bi bi-moon-stars-fill';
        }
    };

    // Carrega preferência salva
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);

    darkBtn?.addEventListener('click', () => {
        const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        localStorage.setItem('theme', next);
    });


    /* ── SIDEBAR MOBILE ────────────────────────────────── */
    const sidebar  = document.getElementById('sidebar');
    const toggle   = document.getElementById('sidebarToggle');
    const overlay  = document.getElementById('sidebarOverlay');
    const closeBtn = document.getElementById('sidebarClose');

    const openSidebar  = () => {
        sidebar?.classList.add('open');
        overlay?.classList.add('show');
    };
    const closeSidebar = () => {
        sidebar?.classList.remove('open');
        overlay?.classList.remove('show');
    };

    toggle?.addEventListener('click', openSidebar);
    overlay?.addEventListener('click', closeSidebar);
    closeBtn?.addEventListener('click', closeSidebar);

    // Marca link ativo na sidebar
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });


    /* ── AUTO-DISMISS ALERTS ───────────────────────────── */
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert?.close();
        }, 4000);
    });


    /* ── CONTADOR DE CARACTERES (textarea) ─────────────── */
    document.querySelectorAll('textarea[maxlength]').forEach(ta => {
        const max     = parseInt(ta.getAttribute('maxlength'));
        const counter = document.createElement('small');
        counter.className = 'text-muted d-block text-end mt-1';
        ta.parentNode.insertBefore(counter, ta.nextSibling);

        const update = () => {
            counter.textContent = `${ta.value.length} / ${max}`;
        };
        ta.addEventListener('input', update);
        update();
    });


    /* ── CONFIRMAÇÃO DE EXCLUSÃO ────────────────────────── */
    document.querySelectorAll('form[data-confirm]').forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!confirm(form.dataset.confirm || 'Confirmar exclusão?')) {
                e.preventDefault();
            }
        });
    });


    /* ── VALIDAÇÃO BÁSICA DE FORMULÁRIOS ────────────────── */
    document.querySelectorAll('form.needs-validation').forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

});