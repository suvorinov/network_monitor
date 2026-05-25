const App = {
    state: {
        sort: { key: null, type: 'string', asc: true },
        toastTimeout: null
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

    initModals() {
        document.getElementById('host-modal')?.addEventListener('click', function (e) {
            if (e.target === this) App.closeHostModal();
        });
        document.getElementById('command-modal')?.addEventListener('click', function (e) {
            if (e.target === this) App.closeCommandModal();
        });
        document.getElementById('settings-modal')?.addEventListener('click', function (e) {
            if (e.target === this) App.closeSettingsModal();
        });
    },

    initHTMXErrorHandler() {
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
        document.querySelectorAll('.status-filter').forEach(btn => {
            btn.addEventListener('click', function () {
                document.querySelectorAll('.status-filter').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                const list = document.getElementById('terminal-list');
                let currentVals = htmx.values(list);
                currentVals['status'] = this.dataset.filter;
                delete currentVals['view'];
                list.setAttribute('hx-vals', JSON.stringify(currentVals));
            });
        });
    },

    initSorting() {
        document.getElementById('terminal-list')?.addEventListener('click', function (e) {
            const header = e.target.closest('th.sort-header');
            if (!header) return;
            const table = header.closest('table');
            if (!table) return;

            const sortKey = header.dataset.sort;
            const sortType = header.dataset.type;
            const isAsc = header.classList.contains('sort-asc');

            App.state.sort.key = sortKey;
            App.state.sort.type = sortType;
            App.state.sort.asc = !isAsc;

            const headers = table.querySelectorAll('th.sort-header');
            headers.forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
                const icon = h.querySelector('i');
                if (icon) icon.className = 'fa-solid fa-sort ml-1 text-[8px] opacity-30';
            });

            if (App.state.sort.asc) {
                header.classList.add('sort-asc');
                const icon = header.querySelector('i');
                if (icon) icon.className = 'fa-solid fa-sort-up ml-1 text-[8px] neon-text';
            } else {
                header.classList.add('sort-desc');
                const icon = header.querySelector('i');
                if (icon) icon.className = 'fa-solid fa-sort-down ml-1 text-[8px] neon-text';
            }

            App.sortTable(table, App.state.sort.key, App.state.sort.type, App.state.sort.asc);
        });

        document.getElementById('terminal-list')?.addEventListener('htmx:afterSettle', function () {
            const table = document.getElementById('cli-table');
            if (!table || !App.state.sort.key) return;
            App.sortTable(table, App.state.sort.key, App.state.sort.type, App.state.sort.asc);
            const headers = table.querySelectorAll('th.sort-header');
            headers.forEach(h => {
                if (h.dataset.sort === App.state.sort.key) {
                    h.classList.add(App.state.sort.asc ? 'sort-asc' : 'sort-desc');
                    const icon = h.querySelector('i');
                    if (icon) {
                        icon.className = App.state.sort.asc
                            ? 'fa-solid fa-sort-up ml-1 text-[8px] neon-text'
                            : 'fa-solid fa-sort-down ml-1 text-[8px] neon-text';
                    }
                } else {
                    const icon = h.querySelector('i');
                    if (icon) icon.className = 'fa-solid fa-sort ml-1 text-[8px] opacity-30';
                }
            });
        });
    },

    sortTable(table, sortKey, type, asc) {
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const datasetKey = 'sort' + sortKey.charAt(0).toUpperCase() + sortKey.slice(1);

        const comparer = (a, b) => {
            let valA = a.dataset[datasetKey] || '';
            let valB = b.dataset[datasetKey] || '';
            if (type === 'number') {
                valA = parseFloat(valA) || 0;
                valB = parseFloat(valB) || 0;
            } else {
                valA = valA.toString();
                valB = valB.toString();
            }
            if (valA < valB) return -1;
            if (valA > valB) return 1;
            return 0;
        };

        rows.sort((a, b) => comparer(a, b) * (asc ? 1 : -1));
        rows.forEach(row => tbody.appendChild(row));
    },

    updateCounters() {
        let online = 0, offline = 0;
        document.querySelectorAll('#cli-table tbody tr').forEach(tr => {
            if (!tr.hasAttribute('data-sort-hostname')) return;
            const statusSpan = tr.querySelector('td:nth-child(4) span');
            if (statusSpan && statusSpan.textContent.includes('ONLINE')) online++;
            else offline++;
        });
        const nodeCountEl = document.getElementById('node-count');
        const offlineCountEl = document.getElementById('offline-count');
        const incidentBadge = document.getElementById('incident-badge');
        if (nodeCountEl) nodeCountEl.innerText = online;
        if (offlineCountEl) offlineCountEl.innerText = offline;
        if (incidentBadge) {
            if (offline > 0) {
                incidentBadge.innerText = offline;
                incidentBadge.classList.remove('hidden');
            } else {
                incidentBadge.classList.add('hidden');
            }
        }
    },

    filterOffline() {
        htmx.ajax('GET', '/htmx/terminals', {
            target: '#terminal-list',
            swap: 'innerHTML',
            values: { status: 'OFFLINE', page: 1, q: '' }
        });
    },

    openHostModal(hostname) {
        const modal = document.getElementById('host-modal');
        const content = document.getElementById('host-modal-content');
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        content.innerHTML = '<div class="panel p-6 text-xs text-center" style="color: var(--text-muted);"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Connecting to terminal...</div>';
        fetch(`/htmx/host_card/${encodeURIComponent(hostname)}`)
            .then(r => { if (!r.ok) throw new Error(); return r.text(); })
            .then(html => { content.innerHTML = html; })
            .catch(() => { content.innerHTML = '<div class="panel p-6 text-xs text-center glow-red">Error loading terminal data.</div>'; });
    },

    closeHostModal() {
        const modal = document.getElementById('host-modal');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    },

    closeCommandModal() {
        const modal = document.getElementById('command-modal');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    },

    setCommand(cmd) {
        const input = document.getElementById('command-input');
        if (input) input.value = cmd;
    },

    sendCommand() {
        const input = document.getElementById('command-input');
        const cmd = input ? input.value.trim() : '';
        if (!cmd) {
            this.showToast('Введите команду', 'error');
            return;
        }
        this.showToast(`Команда "${cmd}" будет выполнена при следующем опросе агента`, 'success');
        const block = document.getElementById('command-result-block');
        const text = document.getElementById('command-result-text');
        if (block) block.classList.remove('hidden');
        if (text) text.textContent = 'Waiting for agent response...';
    },

    showToast(message, type = 'success') {
        let toast = document.getElementById('cyber-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'cyber-toast';
            Object.assign(toast.style, {
                position: 'fixed', bottom: '20px', right: '20px',
                padding: '12px 20px', borderRadius: '6px', fontSize: '12px',
                fontFamily: 'var(--font-mono)', zIndex: '9999',
                transition: 'all 0.3s ease', border: '1px solid var(--border-color)'
            });
            document.body.appendChild(toast);
        }
        if (type === 'success') {
            toast.style.backgroundColor = 'rgba(35, 134, 54, 0.9)';
            toast.style.color = '#fff';
            toast.style.boxShadow = '0 0 15px rgba(63, 185, 80, 0.4)';
        } else {
            toast.style.backgroundColor = 'rgba(248, 81, 73, 0.9)';
            toast.style.color = '#fff';
            toast.style.boxShadow = '0 0 15px rgba(248, 81, 73, 0.4)';
        }
        toast.innerText = `> ${message}`;
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
        clearTimeout(this.state.toastTimeout);
        this.state.toastTimeout = setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
        }, 2500);
    },

    copyConnection(ip, osName, user, btnElement) {
        if (!ip || ip === 'N/A') {
            this.showToast('Error: No IP address', 'error');
            return;
        }
        const username = user !== 'Unknown' ? user : 'admin';
        const command = osName === 'Windows' ? `mstsc /v:${ip}` : `ssh ${username}@${ip}`;
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(command).then(() => {
                this.showToast(`Copied: ${command}`, 'success');
                this.animateButton(btnElement);
            }).catch(() => this.fallbackCopyTextToClipboard(command, btnElement));
        } else {
            this.fallbackCopyTextToClipboard(command, btnElement);
        }
    },

    fallbackCopyTextToClipboard(text, btnElement) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.left = '-999999px';
        textarea.style.top = '-999999px';
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        try {
            if (document.execCommand('copy')) {
                this.showToast(`Copied: ${text}`, 'success');
                this.animateButton(btnElement);
            } else {
                this.showToast('Failed to copy!', 'error');
            }
        } catch {
            this.showToast('Failed to copy!', 'error');
        }
        document.body.removeChild(textarea);
    },

    animateButton(btnElement) {
        if (!btnElement) return;
        const icon = btnElement.querySelector('i');
        if (!icon) return;
        const originalClass = icon.className;
        icon.className = 'fa-solid fa-check';
        btnElement.style.color = 'var(--accent-green)';
        btnElement.style.borderColor = 'var(--accent-green)';
        setTimeout(() => {
            icon.className = originalClass;
            btnElement.style.color = '';
            btnElement.style.borderColor = '';
        }, 1500);
    },

    // Settings

    openSettingsModal() {
        document.getElementById('settings-modal')?.classList.remove('hidden');
        document.getElementById('settings-modal')?.classList.add('flex');
    },

    closeSettingsModal() {
        document.getElementById('settings-modal')?.classList.add('hidden');
        document.getElementById('settings-modal')?.classList.remove('flex');
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

    setPollingInterval(seconds) {
        const list = document.getElementById('terminal-list');
        if (list) {
            list.setAttribute('hx-trigger', `load, every ${seconds}s`);
        }
        localStorage.setItem('cybermonitor-polling', seconds);
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

document.addEventListener('DOMContentLoaded', () => App.init());
