App.initSorting = function () {
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
};

App.sortTable = function (table, sortKey, type, asc) {
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
};

App.updateCounters = function () {
    let online = 0, offline = 0;
    document.querySelectorAll('#cli-table tbody tr[data-status]').forEach(tr => {
        if (tr.dataset.status === 'ONLINE') online++;
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
};

App.filterOffline = function () {
    document.querySelectorAll('.status-filter').forEach(b => b.classList.remove('active'));
    const offlineBtn = document.querySelector('.status-filter[data-filter="OFFLINE"]');
    if (offlineBtn) offlineBtn.classList.add('active');
    const searchInput = document.getElementById('search-input');
    const q = searchInput?.value || '';
    htmx.ajax('GET', '/htmx/terminals', {
        target: '#terminal-list',
        swap: 'innerHTML',
        indicator: '#loading-spinner',
        values: { status: 'OFFLINE', page: 1, q }
    });
};
