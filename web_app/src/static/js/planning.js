const API_URL = '/api/v1/request/view';
const API_BASE_URL = '/api/v1/request';

let currentPage = 1;
let pageSize = 10;
let totalItems = 0;
let totalPages = 0;

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
        const response = await fetch(`${API_URL}/filter/info?request_type=false&status=false&for_planning=true`);
        const data = await response.json();
        const department_data = data.department;

        const select_department_filter = document.getElementById('departmentFilter');
        select_department_filter.innerHTML = '<option value="">Все участки</option>';
        department_data.forEach(department => {
            const option = document.createElement('option');
            option.value = department.id;
            option.innerHTML = `<span>${department.name}</span> (<span>${department.count}<span>)`;
            option.dataset.count = department.count;
            select_department_filter.appendChild(option);
        });

        initializeFilterListeners();
        await loadRequests(1);

    } catch (error) {
        console.error('Ошибка загрузки информации:', error);
        showNotification('Ошибка загрузки информации', 'error');
    }
}

function initializeFilterListeners(page = 1) {
    const departmentFilter = document.getElementById('departmentFilter');

    if (departmentFilter) {
        departmentFilter.addEventListener('change', function(event) {
            const selectedOption = this.options[this.selectedIndex];
            totalItems = Number(selectedOption.dataset.count);
            totalPages = Math.ceil(totalItems / pageSize);
            currentPage = 1;
            loadRequests(1);
        });
    }
}

// Загрузка списка заявок
async function loadRequests(page = 1) {
    try {
        currentPage = page;

        const departmentFilter = document.getElementById('departmentFilter').value || null;
        const params = new URLSearchParams();
        if (departmentFilter) params.append('department', departmentFilter);

        params.append('page', currentPage);
        params.append('page_size', pageSize);

        const response = await fetch(`${API_URL}/list/planning?${params.toString()}`);
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
    const requests = data.planning;
    const rights = data.rights;

    if (rights.download) {
        document.getElementById("download-excel").style.display = "block";
    }

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
            <td>${formatDate(request.deadline)}</td>
            <td>${formatDate(request.created_at)}</td>
            <td>
                <div style="display: flex; flex-direction: column; gap: 5px; width: max-content; text-align: center;">
                    ${rights.view && request.rights.view ? `
                        <a class="btn btn-view-details" href="/request/${request.registration_number}">
                            <i class="fas fa-eye"></i> Просмотр
                        </a>` : ''}
                    ${rights.ready && request.rights.ready ? `
                        <button class="btn btn-ready" onclick="openReadyModal(event, '${request.registration_number}', ${request.item.id})">
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
        const departmentFilter = document.getElementById('departmentFilter').value || null;
        const params = new URLSearchParams();
        if (departmentFilter) params.append('department', departmentFilter);

        const response = await fetch(`/api/v1/download/planning?${params.toString()}`);
        if (response.ok) {
            // Скачиваем файл
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;

            // Получаем имя файла из headers
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `planning.xlsx`;
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }

            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            // Закрываем модальное окно
            closeExportModal();

            // Показываем уведомление об успехе
            showNotification('Файл успешно скачан', 'success');

        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ошибка при загрузке файла');
        }

        showNotification('Данные экспортированы в Excel');
    } catch (error) {
        console.error('Ошибка экспорта:', error);
        showNotification('Ошибка экспорта данных', 'error');
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
        if (e.target === readyModal) {
            closeReadyModal();
        }
    });
});