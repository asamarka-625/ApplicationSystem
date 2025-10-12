async function loadViewInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/request/view/info`);
        const data = await response.json();
        const request_type = data.request_type;
		const status = data.status;
		
        const select1 = document.getElementById('typeFilter');
        info.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            select1.appendChild(option);
        });

        const select2 = document.getElementById('statusFilter');
        request_type.forEach(name=> {
            const option = document.createElement('option');
            option.value = name
            option.textContent = name;
            select2.appendChild(option);
        });

    } catch (error) {
        console.error('Ошибка загрузки информации:', error);
        showNotification('Ошибка загрузки информации', 'error');
    }
}

// Загрузка списка заявок
async function loadRequests() {
    try {
        const statusFilter = document.getElementById('statusFilter').value;
        const typeFilter = document.getElementById('typeFilter').value;
        
        // В реальном приложении - запрос к API с фильтрами
        const response = await fetch(`${API_BASE_URL}/requests/?status=${statusFilter}&request_type=${typeFilter}`);
        const data = await response.json();
        
        displayRequests(data.requests);
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
            <td>${request.items.map(name => name).join('<br>')}</td>
            <td>${getStatusBadge(request.status)}</td>
            <td>${formatDate(request.created_at)}</td>
            <td>${request.deadline ? formatDate(request.deadline) : '-'}</td>
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