const API_URL = '/api/v1/request/view';
const API_BASE_URL = '/api/v1/request';

let currentPage = 1;
let pageSize = 10;
let totalItems = 0;
let totalPages = 0;

let current_department = null;
let current_type = null;
let current_status= null;

function openReadyModal(e, id, item_id) {
    currentReadyRegisterNumber = id;
    currentReadyItemId = item_id;

    const modal = document.getElementById('readyModal');
    const textarea = document.getElementById('readyComment');

    // Сброс формы
    textarea.value = '';
    modal.style.display = 'block';

    // Фокус на текстовом поле
    setTimeout(() => textarea.focus(), 100);
}

function closeReadyModal() {
    const modal = document.getElementById('readyModal');
    modal.style.display = 'none';

    currentReadyRegisterNumber = null;
    currentReadyItemId = null;
}

async function ExecuteRequest() {
    try {
        const comment = document.getElementById('readyComment').value.trim();
        const response = await fetch(`${API_BASE_URL}/execute/${currentReadyRegisterNumber}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id: currentReadyItemId,
                comment: comment
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const answer = await response.json();

        if (answer.status !== 'success') {
            throw new Error(answer.message || 'Ошибка запроса');
        }

        showNotification('Заявка успешно выполнена', 'success');
        document.location.reload();

    } catch (error) {
        console.error('Ошибка выполнения заявки:', error);
        showNotification('Ошибка выполнения заявки', 'error');
    }
}

async function loadViewInfo() {
    try {
        const params = new URLSearchParams();
        if (current_department) params.append('current_department', current_department);
        if (current_type) params.append('current_type', current_type);

        const response = await fetch(`${API_URL}/filter/info?${params.toString()}`);
        const data = await response.json();
        const request_type_data = data.request_type;
		const status_data = data.status;
        const department_data = data.department;

        const select_type_filter = document.getElementById('typeFilter');
        select_type_filter.innerHTML = '<option value="">Все типы</option>';
        request_type_data.forEach(request_type => {
            const option = document.createElement('option');
            option.value = request_type.id;
            option.textContent = request_type.name;
            select_type_filter.appendChild(option);
        });

        const select_status_filter = document.getElementById('statusFilter');
        select_status_filter.innerHTML = '';
        status_data.forEach(status => {
            const option = document.createElement('option');
            option.value = status.id;
            option.innerHTML = `<span>${status.name}</span> (<span>${status.count}<span>)`;
            option.dataset.count = status.count;
            select_status_filter.appendChild(option);
        });

        const select_department_filter = document.getElementById('departmentFilter');
        select_department_filter.innerHTML = '<option value="">Все участки</option>';
        department_data.forEach(department => {
            const option = document.createElement('option');
            option.value = department.id;
            option.textContent = department.name;
            select_department_filter.appendChild(option);
        });

        if (current_department != null || current_type != null || current_status != null) {
            if (current_department != null) {
                select_department_filter.value = current_department;
            }
            if (current_type != null) {
                select_type_filter.value = current_type;
            }
            if (current_status != null) {
                select_status_filter.value = current_status;
            }
        } else {
            initializeFilterListeners();
        }
        await loadRequests(1);

    } catch (error) {
        console.error('Ошибка загрузки информации:', error);
        showNotification('Ошибка загрузки информации', 'error');
    }
}

function initializeFilterListeners() {
    const departmentFilter = document.getElementById('departmentFilter');

    if (statusFilter) {
        statusFilter.addEventListener('change', function(event) {
            const selectedOption = this.options[this.selectedIndex];
            totalItems = Number(selectedOption.dataset.count);
            totalPages = Math.ceil(totalItems / pageSize);
            current_status = selectedOption.value;
            currentPage = 1;
            loadRequests(1);
        });
    }

    if (typeFilter) {
        typeFilter.addEventListener('change', function(event) {
            const selectedOption = this.options[this.selectedIndex];
            current_type = selectedOption.value;
            currentPage = 1;
            loadViewInfo();
        });
    }

    if (departmentFilter) {
        departmentFilter.addEventListener('change', function(event) {
            const selectedOption = this.options[this.selectedIndex];
            current_department = selectedOption.value;
            currentPage = 1;
            loadViewInfo();
        });
    }
}

// Загрузка списка заявок
async function loadRequests(page = 1) {
    try {
        currentPage = page;

        const statusFilter = document.getElementById('statusFilter').value || null;
        const typeFilter = document.getElementById('typeFilter').value || null;
        const departmentFilter = document.getElementById('departmentFilter').value || null;

        // Создаем объект с параметрами
        const params = new URLSearchParams();

        if (statusFilter) params.append('status', statusFilter);
        if (typeFilter) params.append('request_type', typeFilter);
        if (departmentFilter) params.append('department', departmentFilter);

        params.append('page', currentPage);
        params.append('page_size', pageSize);

        const url = `${API_URL}/list/requests?${params.toString()}`;
        const response = await fetch(url);
        const data = await response.json();

        displayRequests(data);
        updatePagination(currentPage);
    } catch (error) {
        console.error('Ошибка загрузки заявок:', error);
        showNotification('Ошибка загрузки заявок', 'error');
    }
}

// Отображение заявок в таблице
function displayRequests(data) {
    const tbody = document.getElementById('requestsTableBody');
    tbody.innerHTML = '';
    const requests = data.requests;
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
            <td>${request.human_registration_number}</td>
            <td>${request.item.name}<br><span class="badge quantity-badge">${request.item.quantity} шт.</span></td>
            <td>${request.request_type.value}</td>
            <td>
                <span class="status-badge status-${request.status.name.toLowerCase()}">
                    ${request.status.value}
                </span>
            </td>
            <td>${request.is_emergency ? '<span class="emergency-badge">Аварийная</span>' : 'Обычная'}</td>
            <td>${formatDate(request.deadline)}</td>
            <td>${formatDate(request.created_at)}</td>
            <td>
                <div style="display: flex; flex-direction: column; gap: 5px; width: max-content; text-align: center;">
                    ${rights.view && request.rights.view ? `
                        <a class="btn btn-view-details" href="/request/${request.registration_number}">
                            <i class="fas fa-eye"></i> Просмотр
                        </a>` : ''}
                    ${rights.planning && request.rights.planning ? `
                        <button class="btn-planning"
                        onclick="openPlanningModal('${request.registration_number}', ${request.item.id}, '${request.item.name.replace('\n', ' ')}', ${request.item.quantity})">
                            <i class="fa-solid fa-pen-to-square"></i> В планирование
                        </button>` : ''}
                    ${rights.ready && request.rights.ready ? `
                        <button class="btn-ready" onclick="openReadyModal(event, '${request.registration_number}', ${request.item.id})">
                            <i class="fa-solid fa-thumbs-up"></i> Готово
                        </button> ` : ''}
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

let currentItemId = null;

function openPlanningModal(registration_number, itemId, itemName, itemQuantity) {
    document.getElementById('planningModal').dataset.registrationNumber = registration_number;
    currentItemId = itemId;
    document.getElementById('modalItemName').textContent = itemName;
    document.getElementById('modalItemQuantity').textContent = itemQuantity;

    // Установка минимальной даты - сегодня
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('deadlineDate').min = today;
    document.getElementById('deadlineDate').value = today;

    const modal = document.getElementById('planningModal');
    modal.style.display = 'block';
}

function closePlanningModal() {
    const modal = document.getElementById('planningModal');
    modal.style.display = 'none';
    currentItemId = null;
}

async function addToPlanning() {
    if (currentItemId) {
        const deadlineDate = document.getElementById('deadlineDate').value;
        const registration_number = document.getElementById('planningModal').dataset.registrationNumber;

        if (!deadlineDate) {
            alert('Пожалуйста, выберите дату выполнения');
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/planning/${registration_number}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    item_id: currentItemId,
                    deadline: deadlineDate
                })
            });

            if (response.ok) {
                window.location.reload();

            } else {
                throw new Error('Ошибка при добавлении в планирование');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Произошла ошибка при добавлении в планирование');
        }
    }
}

function updatePagination(page = 1) {
    currentPage = page;

    // Обновляем информацию о пагинации
    const startItem = (currentPage - 1) * pageSize + 1;
    const endItem = Math.min(currentPage * pageSize, totalItems);
    document.getElementById('paginationInfo').textContent =
        `Показано ${startItem}-${endItem} из ${totalItems} заявок`;

    // Обновляем кнопки навигации
    document.getElementById('firstPage').disabled = currentPage === 1;
    document.getElementById('prevPage').disabled = currentPage === 1;
    document.getElementById('nextPage').disabled = currentPage === totalPages || totalPages === 0;
    document.getElementById('lastPage').disabled = currentPage === totalPages || totalPages === 0;

    // Создаем номера страниц
    const paginationNumbers = document.getElementById('paginationNumbers');
    paginationNumbers.innerHTML = '';

    // Логика отображения номеров страниц (показываем 5 страниц)
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);

    // Корректируем если мы в конце
    if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
    }

    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `page-number ${i === currentPage ? 'active' : ''}`;
        pageBtn.textContent = i;
        pageBtn.onclick = () => loadRequests(i);
        paginationNumbers.appendChild(pageBtn);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    loadViewInfo();

    document.getElementById('firstPage').addEventListener('click', () => loadRequests(1));
    document.getElementById('prevPage').addEventListener('click', () => loadRequests(currentPage - 1));
    document.getElementById('nextPage').addEventListener('click', () => loadRequests(currentPage + 1));
    document.getElementById('lastPage').addEventListener('click', () => loadRequests(totalPages));

    // Обработчик изменения размера страницы
    document.getElementById('pageSize').addEventListener('change', function(e) {
        pageSize = parseInt(e.target.value);
        currentPage = 1; // Сбрасываем на первую страницу
        loadRequests(currentPage);
    });

    const modalPlanning = document.getElementById('planningModal');
    const closeBtnPlanning = modalPlanning.querySelector('.close');
    const cancelBtnPlanning = document.getElementById('cancelPlanningBtn');
    const addBtnPlanning = document.getElementById('addToPlanningBtn');

    closeBtnPlanning.onclick = closePlanningModal;
    cancelBtnPlanning.onclick = closePlanningModal;
    addBtnPlanning.onclick = addToPlanning;

    const readyModal = document.getElementById('readyModal');
    const readyForm = document.getElementById('readyForm');
    const cancelReady = document.getElementById('cancelReady');
    const closeBtnReady = readyModal.querySelector('.close');

    // Обработчик отправки формы
    readyForm.addEventListener('submit', function(event) {
        event.preventDefault();
        ExecuteRequest();
    });

    // Обработчики закрытия модального окна
    cancelReady.addEventListener('click', closeReadyModal);
    closeBtnReady.addEventListener('click', closeReadyModal);

    // Закрытие при клике вне модального окна
    window.addEventListener('click', function(e) {
        if (e.target === modalPlanning) {
            closePlanningModal();
        }

        if (e.target === readyModal) {
            closeReadyModal();
        }
    });
});