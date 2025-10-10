// Получаем элементы
const searchInput = document.getElementById('requestTitle');
const suggestionsContainer = document.getElementById('suggestions');

// Накладываем событие на ввод с debounce
let searchTimeout;
searchInput.addEventListener('input', function(event) {
    const searchTerm = event.target.value.trim();

    // Очищаем предыдущий таймер
    clearTimeout(searchTimeout);

    // Если строка не пустая, отправляем запрос через 300ms
    if (searchTerm.length > 2) {
        searchTimeout = setTimeout(() => {
            searchItems(searchTerm);
        }, 300);
    } else {
        hideSuggestions();
    }
});

// Функция для отправки запроса
async function searchItems(query) {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE_URL}/item/?search=${encodeURIComponent(query)}`);

        if (!response.ok) {
            throw new Error('Ошибка сети');
        }

        const results = await response.json();
        displaySuggestions(results);

    } catch (error) {
        console.error('Ошибка поиска:', error);
        hideSuggestions();
    } finally {
        showLoading(false);
    }
}

// Функция для отображения подсказок
function displaySuggestions(items) {
    if (!items || items.length === 0) {
        hideSuggestions();
        return;
    }

    const suggestionsHTML = items.map(item => `
        <div class="suggestion-item" data-value="${item.title || item.name}">
            ${item.title || item.name}
        </div>
    `).join('');

    suggestionsContainer.innerHTML = suggestionsHTML;
    suggestionsContainer.style.display = 'block';
}

// Функция для скрытия подсказок
function hideSuggestions() {
    suggestionsContainer.style.display = 'none';
}

// Обработчик клика по подсказке
suggestionsContainer.addEventListener('click', function(event) {
    if (event.target.classList.contains('suggestion-item')) {
        const value = event.target.getAttribute('data-value');
        searchInput.value = value;
        hideSuggestions();
    }
});

// Скрываем подсказки при клике вне input
document.addEventListener('click', function(event) {
    if (!searchInput.contains(event.target) && !suggestionsContainer.contains(event.target)) {
        hideSuggestions();
    }
});

// Дополнительные обработчики для клавиатуры
searchInput.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        hideSuggestions();
    }
});

// Функции для индикации загрузки (заглушки)
function showLoading(show) {
    // Реализуйте отображение индикатора загрузки
    if (show) {
        console.log('Показываем загрузку...');
    } else {
        console.log('Скрываем загрузку...');
    }
}

async function loadJudicialSites() {
    try {
        const response = await fetch(`${API_BASE_URL}/request/info`);
        const data = await response.json();
        console.log(data);
        const info = data.departament;
        const request_type = data.request_type;

        const select1 = document.getElementById('judicialSite');
        info.forEach(site => {
            const option = document.createElement('option');
            option.value = site.code;
            option.textContent = site.name;
            select1.appendChild(option);
        });

        const select2 = document.getElementById('requestType');
        request_type.forEach(site => {
            const option = document.createElement('option');
            option.value = site;
            option.textContent = site;
            select2.appendChild(option);
        });

    } catch (error) {
        console.error('Ошибка загрузки судебных участков:', error);
        showNotification('Ошибка загрузки справочников', 'error');
    }
}

// Обработка отправки формы заявки
async function handleRequestSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const requestData = {
        title: formData.get('title'),
        description: formData.get('description'),
        request_type: formData.get('requestType'),
        judicial_site_id: parseInt(formData.get('judicialSiteId')),
        is_emergency: formData.get('requestType') === 'EMERGENCY',
        deadline: formData.get('deadline') || null
    };
    
    try {
        // В реальном приложении - отправка на сервер
        const response = await fetch(`${API_BASE_URL}/requests/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (response.ok) {
            showNotification('Заявка успешно создана!');
            resetForm();
            showSection('requests');
            loadRequests();
        } else {
            throw new Error('Ошибка создания заявки');
        }
    } catch (error) {
        console.error('Ошибка создания заявки:', error);
        showNotification('Ошибка создания заявки', 'error');
    }
}

// Загрузка списка заявок
async function loadRequests() {
    try {
        const statusFilter = document.getElementById('statusFilter').value;
        const typeFilter = document.getElementById('typeFilter').value;
        
        // В реальном приложении - запрос к API с фильтрами
        const response = await fetch(`${API_BASE_URL}/requests/?status=${statusFilter}&request_type=${typeFilter}`);
        const requests = await response.json();
        
        displayRequests(requests);
    } catch (error) {
        console.error('Ошибка загрузки заявок:', error);
        showNotification('Ошибка загрузки заявок', 'error');
    }
}

// Отображение заявок в таблице
function displayRequests(requests) {
    const tbody = document.getElementById('requestsTableBody');
    tbody.innerHTML = '';
    
    if (requests.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">Заявки не найдены</td></tr>';
        return;
    }
    
    requests.forEach(request => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${request.registration_number}</td>
            <td>${getRequestTypeText(request.request_type)}</td>
            <td>${request.title}</td>
            <td>${getStatusBadge(request.status)}</td>
            <td>${formatDate(request.created_at)}</td>
            <td>${request.deadline ? formatDate(request.deadline) : '-'}</td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="viewRequest(${request.id})">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Просмотр деталей заявки
async function viewRequest(requestId) {
    try {
        const response = await fetch(`${API_BASE_URL}/requests/${requestId}`);
        const request = await response.json();
        
        displayRequestModal(request);
    } catch (error) {
        console.error('Ошибка загрузки заявки:', error);
        showNotification('Ошибка загрузки заявки', 'error');
    }
}

function displayRequestModal(request) {
    const modalBody = document.getElementById('requestModalBody');
    
    modalBody.innerHTML = `
        <div class="request-details">
            <div class="detail-row">
                <label>Номер заявки:</label>
                <span>${request.registration_number}</span>
            </div>
            <div class="detail-row">
                <label>Тип заявки:</label>
                <span>${getRequestTypeText(request.request_type)}</span>
            </div>
            <div class="detail-row">
                <label>Статус:</label>
                <span>${getStatusBadge(request.status)}</span>
            </div>
            <div class="detail-row">
                <label>Название:</label>
                <span>${request.title}</span>
            </div>
            <div class="detail-row">
                <label>Описание:</label>
                <p>${request.description || 'Не указано'}</p>
            </div>
            <div class="detail-row">
                <label>Дата создания:</label>
                <span>${formatDate(request.created_at)}</span>
            </div>
            <div class="detail-row">
                <label>Срок исполнения:</label>
                <span>${request.deadline ? formatDate(request.deadline) : 'Не установлен'}</span>
            </div>
            ${request.is_emergency ? `
            <div class="detail-row emergency">
                <label><i class="fas fa-exclamation-triangle"></i> Аварийная:</label>
                <span>Да</span>
            </div>
            ` : ''}
        </div>
        
        ${request.materials && request.materials.length > 0 ? `
        <div class="materials-section">
            <h3>Перемещенные материалы</h3>
            <div class="materials-list">
                ${request.materials.map(material => `
                    <div class="material-item">
                        <strong>${material.material_name}</strong>
                        <span>${material.quantity} ${material.unit}</span>
                        <small>${formatDate(material.issued_at)}</small>
                    </div>
                `).join('')}
            </div>
        </div>
        ` : ''}
    `;
    
    document.getElementById('requestModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('requestModal').style.display = 'none';
}

function resetForm() {
    document.getElementById('requestForm').reset();
    document.querySelector('.emergency-section').style.display = 'none';
}

// Экспорт в Excel
async function exportToExcel() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/export/excel`);
        const blob = await response.blob();
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `заявки_${new Date().toISOString().split('T')[0]}.xlsx`;
        
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showNotification('Данные экспортированы в Excel');
    } catch (error) {
        console.error('Ошибка экспорта:', error);
        showNotification('Ошибка экспорта данных', 'error');
    }
}