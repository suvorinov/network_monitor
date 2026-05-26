App.showToast = function (message, type = 'success') {
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
    clearTimeout(App.state.toastTimeout);
    App.state.toastTimeout = setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
    }, 2500);
};

App.copyConnection = function (ip, osName, user, btnElement) {
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
};

App.fallbackCopyTextToClipboard = function (text, btnElement) {
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
};

App.animateButton = function (btnElement) {
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
};
