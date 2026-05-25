const Toast = {
    container: null,

    init() {
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'fixed bottom-4 right-4 z-50 flex flex-col space-y-2';
            document.body.appendChild(this.container);
        }
    },

    show(message, type = 'info') {
        const toast = document.createElement('div');
        const colors = {
            success: 'bg-green-900/90 border-green-500',
            error: 'bg-red-900/90 border-red-500',
            info: 'bg-gray-800/90 border-gray-500'
        };
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            info: 'fa-info-circle'
        };

        toast.className = `${colors[type] || colors.info} border text-white px-4 py-3 rounded shadow-lg flex items-center space-x-3 toast-animate`;
        toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i> <span>${message}</span>`;
        
        this.container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100px)';
            toast.style.transition = 'all 0.5s ease';
            setTimeout(() => toast.remove(), 500);
        }, 3000);
    }
};

const Clipboard = {
    copy(text) {
        if (!text) return;

        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(() => {
                window.showToast && window.showToast('Copied to clipboard', 'success');
            }).catch(() => {
                this.fallback(text);
            });
        } else {
            this.fallback(text);
        }
    },

    fallback(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const success = document.execCommand('copy');
            window.showToast && window.showToast(
                success ? 'Copied to clipboard' : 'Failed to copy',
                success ? 'success' : 'error'
            );
        } catch (err) {
            window.showToast && window.showToast('Failed to copy', 'error');
        }
        document.body.removeChild(textArea);
    }
};

const Utils = {
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    },

    getApiKey() {
        return this.getCookie('api_key');
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Toast.init();
    window.showToast = Toast.show.bind(Toast);
});

window.Toast = Toast;
window.Clipboard = Clipboard;
window.Utils = Utils;