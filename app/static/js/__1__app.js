function copyConnection(ip, osName, user, btnElement) {
    if (!ip || ip === 'N/A') {
        showToast('Error: No IP address', 'error');
        return;
    }

    let command = '';
    const username = user !== 'Unknown' ? user : 'admin'; // Дефолтный юзер, если не определился

    if (osName === 'Windows') {
        // Для Windows генерируем команду RDP
        command = `mstsc /v:${ip}`;
    } else {
        // Для Linux генерируем SSH (подставляем текущего юзера)
        command = `ssh ${username}@${ip}`;
    }

    // Используем современный API для копирования
    navigator.clipboard.writeText(command).then(() => {
        showToast(`Copied: ${command}`, 'success');
        
        // Визуальный фидбек на кнопке
        const icon = btnElement.querySelector('i');
        const originalClass = icon.className;
        icon.className = 'fa-solid fa-check';
        btnElement.style.color = 'var(--accent-green)';
        btnElement.style.borderColor = 'var(--accent-green)';
        
        setTimeout(() => {
            icon.className = originalClass;
            btnElement.style.color = '';
            btnElement.style.borderColor = '';
        }, 1500);

    }).catch(err => {
        showToast('Failed to copy!', 'error');
        console.error('Copy error:', err);
    });
}

// Функция показа "Тоста" (уведомления)
let toastTimeout;
function showToast(message, type = 'success') {
    let toast = document.getElementById('cyber-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'cyber-toast';
        toast.style.position = 'fixed';
        toast.style.bottom = '20px';
        toast.style.right = '20px';
        toast.style.padding = '12px 20px';
        toast.style.borderRadius = '6px';
        toast.style.fontSize = '12px';
        toast.style.fontFamily = 'var(--font-mono)';
        toast.style.zIndex = '9999';
        toast.style.transition = 'all 0.3s ease';
        toast.style.border = '1px solid var(--border-color)';
        document.body.appendChild(toast);
    }

    // Стили в зависимости от типа
    if (type === 'success') {
        toast.style.backgroundColor = 'rgba(35, 134, 54, 0.9)'; // accent-green-dim
        toast.style.color = '#fff';
        toast.style.boxShadow = '0 0 15px rgba(63, 185, 80, 0.4)';
    } else {
        toast.style.backgroundColor = 'rgba(248, 81, 73, 0.9)'; // danger
        toast.style.color = '#fff';
        toast.style.boxShadow = '0 0 15px rgba(248, 81, 73, 0.4)';
    }

    toast.innerText = `> ${message}`;
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';

    // Скрываем через 2.5 секунды
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
    }, 2500);
}
