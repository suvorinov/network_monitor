const App = {
    state: {
        sort: { key: null, type: 'string', asc: true },
        toastTimeout: null,
        pollingTimer: null,
        pollingInterval: 10
    },

    init() {
        this.initClock();
        this.initModals();
        this.initHTMXErrorHandler();
        this.initFilters();
        this.initSorting();
        this.loadSettings();
    },

    initClock() {
        const el = document.getElementById('current-time');
        if (!el) return;
        function update() { el.textContent = new Date().toLocaleTimeString('ru-RU'); }
        setInterval(update, 1000);
        update();
    },

    initHTMXErrorHandler() {
        document.body.addEventListener('htmx:configRequest', (evt) => {
            if (evt.detail.method !== 'GET') {
                const meta = document.querySelector('meta[name="csrf-token"]');
                if (meta) {
                    evt.detail.headers['X-CSRF-Token'] = meta.content;
                }
            }
        });
        document.body.addEventListener('htmx:afterRequest', (evt) => {
            if (evt.detail.failed) {
                App.showToast('Ошибка соединения с сервером', 'error');
            }
        });
        document.body.addEventListener('htmx:afterSettle', () => {
            App.updateCounters();
        });
    },

    initFilters() {
        document.getElementById('filters')?.addEventListener('click', function (e) {
            const btn = e.target.closest('.status-filter');
            if (!btn) return;
            document.querySelectorAll('.status-filter').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    },

    restartPollingTimer() {
        if (this.state.pollingTimer) clearInterval(this.state.pollingTimer);
        const poll = () => {
            const activeFilter = document.querySelector('.status-filter.active');
            const searchInput = document.getElementById('search-input');
            const status = activeFilter?.dataset?.filter || 'ALL';
            const q = searchInput?.value || '';
            htmx.ajax('GET', '/htmx/terminals', {
                target: '#terminal-list',
                swap: 'innerHTML',
                indicator: '#loading-spinner',
                values: { page: 1, status, q }
            });
        };
        poll();
        this.state.pollingTimer = setInterval(poll, this.state.pollingInterval * 1000);
    },

    setPollingInterval(seconds) {
        this.state.pollingInterval = seconds;
        localStorage.setItem('cybermonitor-polling', seconds);
        this.restartPollingTimer();
    },

    setTheme(theme) {
        const html = document.documentElement;
        if (theme === 'light') {
            html.classList.add('theme-light');
        } else {
            html.classList.remove('theme-light');
        }
        document.querySelectorAll('#settings-modal .btn-terminal').forEach(b => {
            b.style.backgroundColor = 'var(--accent-green-dim)';
        });
        const btn = document.getElementById(`theme-${theme}`);
        if (btn) btn.style.backgroundColor = 'var(--border-color)';
        localStorage.setItem('cybermonitor-theme', theme);
    },

    loadSettings() {
        const theme = localStorage.getItem('cybermonitor-theme');
        if (theme === 'light') {
            document.documentElement.classList.add('theme-light');
            const btn = document.getElementById('theme-light');
            if (btn) btn.style.backgroundColor = 'var(--border-color)';
        } else {
            const btn = document.getElementById('theme-dark');
            if (btn) btn.style.backgroundColor = 'var(--border-color)';
        }
        const polling = parseInt(localStorage.getItem('cybermonitor-polling')) || 10;
        const select = document.getElementById('polling-interval');
        if (select) {
            select.value = polling;
            this.setPollingInterval(polling);
        }
    }
};
