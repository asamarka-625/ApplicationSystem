function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    const messageEl = document.getElementById('notificationMessage');
    
    messageEl.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.remove('hidden');
    
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 5000);
}

function formatDate(dateString, full=true) {
    const date = new Date(dateString);

    if (full) {
        return date.toLocaleDateString('ru-RU') + ' ' + date.toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });
    } else {
        return date.toLocaleDateString('ru-RU');
    }
}

async function logout() {
    try {
        const response = await fetch('/logout', {
            method: 'POST',
            credentials: 'include'  // Важно для отправки кук
        });

        if (response.ok) {
            // Очищаем localStorage на всякий случай
            localStorage.removeItem('access_token');
            // Перенаправляем на страницу логина
            window.location.href = '/login';
        } else {
            alert('Logout failed!');
        }
    } catch (error) {
        console.error('Logout error:', error);
    }
}
