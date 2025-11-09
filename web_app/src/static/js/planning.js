const API_URL = '/api/v1/request/view';
const API_BASE_URL = '/api/v1/request';

async function ExecuteRequest(e, registration_number, item_id) {
    try {
        const response = await fetch(`${API_BASE_URL}/execute/${registration_number}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({id: item_id})
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.status !== 'success') {
            throw new Error(data.message || 'Ошибка запроса');
        }

        const buttonContainer = e.target.closest('div');
        const buttons = buttonContainer.querySelectorAll('a, button');

        buttons.forEach(button => {
            if (!button.classList.contains('btn-view-details')) {
                button.style.display = 'none';
            }
        });

        showNotification('Заявка успешно выполнена', 'success');
        document.location.reload();

    } catch (error) {
        console.error('Ошибка выполнения заявки:', error);
        showNotification('Ошибка выполнения заявки', 'error');
    }
}

async function loadViewInfo() {
    try {
        const response = await fetch(`${API_URL}/filter/info`);
        const data = await response.json();
        const request_type_data = data.request_type;
		const status_data = data.status;

        const select_type_filter = document.getElementById('typeFilter');
        request_type_data.forEach(request_type => {
            const option = document.createElement('option');
            option.value = request_type.id;
            option.textContent = request_type.name;
            select_type_filter.appendChild(option);
        });

        const select_status_filter = document.getElementById('statusFilter');
        status_data.forEach(status => {
            const option = document.createElement('option');
            option.value = status.id
            option.textContent = status.name;
            select_status_filter.appendChild(option);
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
        const response = await fetch(`${API_URL}/list/planning?status=${statusFilter}&request_type=${typeFilter}`);
        const data = await response.json();

        displayRequests(data);
    } catch (error) {
        console.error('Ошибка загрузки заявок:', error);
        showNotification('Ошибка загрузки заявок', 'error');
    }
}

// Отображение заявок в таблице
function displayRequests(data) {
    const tbody = document.getElementById('requestsTableBody');
    tbody.innerHTML = '';
    const requests = data.planning;
    const rights = data.rights;

    if (requests.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">Заявки не найдены</td></tr>';
        return;
    }

    requests.forEach(request => {
        const row = document.createElement('tr');
		row.classList.add(`tr-${request.actual_status}`);
        row.innerHTML = `
            <td>${request.registration_number}</td>
            <td>${request.item.name}<br><span class="badge quantity-badge">${request.item.quantity} шт.</span></td>
            <td>${request.request_type.value}</td>
            <td>${formatDate(request.deadline)}</td>
            <td>${formatDate(request.created_at)}</td>
            <td>
                <div style="display: flex; flex-direction: column; gap: 5px; width: max-content; text-align: center;">
                    ${rights.view && request.rights.view ? `
                        <a class="btn-view-details" href="/request/${request.registration_number}">
                            <i class="fas fa-eye"></i> Просмотр
                        </a>` : ''}
                    ${rights.ready && request.rights.ready ? `
                        <button class="btn-ready" onclick="ExecuteRequest(event, '${request.registration_number}', ${request.item.id})">
                            <i class="fa-solid fa-thumbs-up"></i> Готово
                        </button> ` : ''}
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Экспорт в Excel
async function exportToExcel() {
    try {
        const response = await fetch(`${API_URL}/dashboard/export/excel`);
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

document.addEventListener('DOMContentLoaded', function() {
    loadViewInfo();
    loadRequests();
});