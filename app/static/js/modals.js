App.initModals = function () {
    document.getElementById('host-modal')?.addEventListener('click', function (e) {
        if (e.target === this) App.closeHostModal();
    });
    document.getElementById('command-modal')?.addEventListener('click', function (e) {
        if (e.target === this) App.closeCommandModal();
    });
    document.getElementById('settings-modal')?.addEventListener('click', function (e) {
        if (e.target === this) App.closeSettingsModal();
    });
};

App.openHostModal = function (hostname) {
    const modal = document.getElementById('host-modal');
    const content = document.getElementById('host-modal-content');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    content.innerHTML = '<div class="panel p-6 text-xs text-center text-muted"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Connecting to terminal...</div>';
    htmx.ajax('GET', `/htmx/host_card/${encodeURIComponent(hostname)}`, {
        target: '#host-modal-content',
        swap: 'innerHTML'
    });
};

App.closeHostModal = function () {
    const modal = document.getElementById('host-modal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
};

App.closeCommandModal = function () {
    const modal = document.getElementById('command-modal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
};

App.setCommand = function (cmd) {
    const input = document.getElementById('command-input');
    if (input) input.value = cmd;
};

App.sendCommand = function () {
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
};

App.openSettingsModal = function () {
    document.getElementById('settings-modal')?.classList.remove('hidden');
    document.getElementById('settings-modal')?.classList.add('flex');
};

App.closeSettingsModal = function () {
    document.getElementById('settings-modal')?.classList.add('hidden');
    document.getElementById('settings-modal')?.classList.remove('flex');
};
