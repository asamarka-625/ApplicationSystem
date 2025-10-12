// Конфигурация API
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Текущий пользователь (в реальном приложении получать из аутентификации)
let currentUser = {
    id: 1,
    full_name: 'Иванов Иван Иванович',
    role: 'JUDGE',
    email: 'judge@example.com'
};

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadDashboardData();
});

function initializeApp() {
    // Установка информации о пользователе
    document.getElementById('userName').textContent = currentUser.full_name;
    document.getElementById('userRole').textContent = getUserRoleText(currentUser.role);
    
    // Загрузка справочников
    loadJudicialSites();
}

function setupEventListeners() {
    // Навигация
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('href').substring(1);
            showSection(target);
        });
    });
    
    // Форма создания заявки
    document.getElementById('requestForm').addEventListener('submit', handleRequestSubmit);
    
    // Фильтры заявок
    document.getElementById('statusFilter').addEventListener('change', loadRequests);
    document.getElementById('typeFilter').addEventListener('change', loadRequests);
    
    // Статистика
    document.getElementById('statsPeriod').addEventListener('change', loadStatistics);
    
    // Модальное окно
    document.querySelector('.close').addEventListener('click', closeModal);
    window.addEventListener('click', function(e) {
        const modal = document.getElementById('requestModal');
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // Обработка типа заявки для показа/скрытия аварийной секции
    document.getElementById('requestType').addEventListener('change', function() {
        const emergencySection = document.querySelector('.emergency-section');
        const isEmergency = this.value === 'Аварийная';
        emergencySection.style.display = isEmergency ? 'block' : 'none';
    });
}

function getUserRoleText(role) {
    const roles = {
        'JUDGE': 'Мировой судья',
        'SECRETARY': 'Секретарь суда',
        'MANAGEMENT': 'Руководство управления',
        'EXECUTOR': 'Исполнитель',
        'FBU': 'Сотрудник ФБУ',
        'COMMITTEE': 'Сотрудник комитета'
    };
    return roles[role] || role;
}

// Утилитарные функции
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU') + ' ' + date.toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getStatusBadge(status) {
    const statuses = {
        'DRAFT': { text: 'Черновик', class: 'status-draft' },
        'REGISTERED': { text: 'Зарегистрирована', class: 'status-registered' },
        'IN_PROGRESS': { text: 'В работе', class: 'status-in_progress' },
        'COMPLETED': { text: 'Выполнена', class: 'status-completed' },
        'CANCELLED': { text: 'Отменена', class: 'status-cancelled' }
    };
    
    const statusInfo = statuses[status] || { text: status, class: '' };
    return `<span class="status-badge ${statusInfo.class}">${statusInfo.text}</span>`;
}

function getRequestTypeText(type) {
    const types = {
        'MATERIAL': 'Материально-техническое',
        'TECHNICAL': 'Техническое обслуживание',
        'OPERATIONAL': 'Эксплуатационное',
        'EMERGENCY': 'Аварийная'
    };
    return types[type] || type;
}