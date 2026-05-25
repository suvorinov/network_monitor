let modalHostname = '';
let toastTimeout;
let resultCheckInterval;
let currentSortState = {
    key: null,
    type: 'string',
    asc: true
};
let onlineCount = 0;
let offlineCount = 0;


function copyConnection(ip, osName, user, btnElement) {
    if (!ip || ip === 'N/A') {
        showToast('Error: No IP address', 'error');
        return;
    }

    let command = '';
    const username = user !== 'Unknown' ? user : 'admin'; // Дефолтный юзер, если не определился

    if (osName === 'Windows') {
        command = `mstsc /v:${ip}`;
    } else {
        command = `ssh ${username}@${ip}`;
    }

    // Фоллбэк для HTTP (небезопасный контекст), так как navigator.clipboard undefined
    if (navigator.clipboard && window.isSecureContext) {
        // Если HTTPS или localhost - используем современный метод
        navigator.clipboard.writeText(command).then(() => {
            showToast(`Copied: ${command}`, 'success');
            animateButton(btnElement);
        }).catch(err => {
            fallbackCopyTextToClipboard(command, btnElement);
        });
    } else {
        // Если HTTP (наша локалка) - используем старый трюк с textarea
        fallbackCopyTextToClipboard(command, btnElement);
    }
}

// Функция резервного копирования через DOM
function fallbackCopyTextToClipboard(text, btnElement) {
    let textarea = document.createElement("textarea");
    textarea.value = text;
    
    // Делаем её невидимой, но доступной для выделения
    textarea.style.position = "fixed";
    textarea.style.left = "-999999px";
    textarea.style.top = "-999999px";
    document.body.appendChild(textarea);
    
    textarea.focus();
    textarea.select();

    try {
        let successful = document.execCommand('copy');
        if (successful) {
            showToast(`Copied: ${text}`, 'success');
            animateButton(btnElement);
        } else {
            showToast('Failed to copy!', 'error');
        }
    } catch (err) {
        showToast('Failed to copy!', 'error');
    }
    
    document.body.removeChild(textarea);
}

// Визуальная анимация кнопки
function animateButton(btnElement) {
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
}

// Функция показа "Тоста" (уведомления)
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

    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
    }, 2500);
}

function openHostModal(hostname) {
    const modal = document.getElementById('host-modal');
    const content = document.getElementById('host-modal-content');
    
    // Показываем модалку с загрузкой
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    content.innerHTML = '<div class="panel p-6 text-xs text-center" style="color: var(--text-muted);"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Connecting to terminal...</div>';

    // Делаем прямой запрос к нашему API
    fetch(`/htmx/host_card/${hostname}`)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.text();
        })
        .then(html => {
            content.innerHTML = html; // Вставляем отрендеренный HTML
        })
        .catch(error => {
            content.innerHTML = '<div class="panel p-6 text-xs text-center glow-red">Error loading terminal data.</div>';
            console.error('Error fetching host card:', error);
        });
}

function closeHostModal() {
    const modal = document.getElementById('host-modal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}


// Закрытие по клику вне карточки
document.getElementById('host-modal').addEventListener('click', function(e) {
    if (e.target === this) closeHostModal();
});

    // Закрытие модалки по клику вне её области
document.getElementById('command-modal').addEventListener('click', function(e) {
    if (e.target === this) closeCommandModal();
});
