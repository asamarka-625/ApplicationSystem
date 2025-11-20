const API_URL = '/api/v1/request/view';
const API_BASE_URL = '/api/v1/request';

let currentPage = 1;
let pageSize = 10;
let totalItems = 0;
let totalPages = 0;

let current_department = null;
let current_type = null;
let current_status= null;

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
        if (department_data) {
            select_department_filter.innerHTML = '<option value="">Все участки</option>';
            department_data.forEach(department => {
                const option = document.createElement('option');
                option.value = department.id;
                option.textContent = department.name;
                select_department_filter.appendChild(option);
            });
            select_department_filter.style.display = 'block';
        }

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
    const statusFilter = document.getElementById('statusFilter');
    const typeFilter = document.getElementById('typeFilter');
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

    if (departmentFilter && departmentFilter.style.display != 'none') {
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
            <td>${request.request_type.value}</td>
            <td>
                <span class="status-badge status-${request.status.name.toLowerCase()}">
                    ${request.status.value}
                </span>
            </td>
            <td>${request.is_emergency ? '<span class="emergency-badge">Аварийная</span>' : 'Обычная'}</td>
            <td>${formatDate(request.created_at)}</td>
            <td>
                <a class="btn btn-view-details" href="/request/${request.registration_number}">
                    <i class="fas fa-eye"></i> Просмотр
                </a>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function openExportModal() {
    // Устанавливаем даты по умолчанию
    const today = new Date();
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(today.getMonth() - 1);

    // Форматируем даты для input type="date"
    document.getElementById('exportDateFrom').value = formatDateForInput(oneMonthAgo);
    document.getElementById('exportDateUntil').value = formatDateForInput(today);

    // Показываем модальное окно
    const modal = document.getElementById('exportModal');
    modal.style.display = 'block';

    // Блокируем прокрутку body
    document.body.style.overflow = 'hidden';
}

// Функция для закрытия модального окна
function closeExportModal() {
    const modal = document.getElementById('exportModal');
    modal.style.display = 'none';

    // Восстанавливаем прокрутку body
    document.body.style.overflow = 'auto';
}

// Функция для форматирования даты в формат YYYY-MM-DD
function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Функция для экспорта в Excel
async function exportToExcel() {
    const dateFrom = document.getElementById('exportDateFrom').value;
    const dateUntil = document.getElementById('exportDateUntil').value;

    // Валидация дат
    if (!dateFrom || !dateUntil) {
        showNotification('Пожалуйста, выберите обе даты', 'error');
        return;
    }

    if (new Date(dateFrom) > new Date(dateUntil)) {
        showNotification('Дата "с" не может быть больше даты "по"', 'error');
        return;
    }

    // Получаем текущие фильтры из таблицы
    const statusFilter = document.getElementById('statusFilter').value || null;
    const typeFilter = document.getElementById('typeFilter').value || null;
    const departmentFilter = document.getElementById('departmentFilter').value || null;

    // Собираем параметры
    const params = new URLSearchParams();
    params.append('date_from', dateFrom);
    params.append('date_until', dateUntil);

    if (statusFilter) params.append('status', statusFilter);
    if (typeFilter) params.append('request_type', typeFilter);
    if (departmentFilter) params.append('department', departmentFilter);

    try {
        // Показываем индикатор загрузки
        const downloadBtn = document.querySelector('#exportModal .btn-primary');
        const originalText = downloadBtn.innerHTML;
        downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Загрузка...';
        downloadBtn.disabled = true;

        // Выполняем запрос
        const response = await fetch(`/api/v1/download/requests?${params.toString()}`, {
            method: 'GET'
        });

        if (response.ok) {
            // Скачиваем файл
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;

            // Получаем имя файла из headers
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `requests_${dateFrom}_${dateUntil}.xlsx`;
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

    } catch (error) {
        console.error('Ошибка экспорта:', error);
        showNotification(error.message || 'Ошибка при экспорте данных', 'error');
    } finally {
        // Восстанавливаем кнопку
        const downloadBtn = document.querySelector('#exportModal .btn-primary');
        if (downloadBtn) {
            downloadBtn.innerHTML = '<i class="fas fa-download"></i> Скачать Excel';
            downloadBtn.disabled = false;
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

    const today = new Date().toISOString().split('T')[0];
    document.getElementById('exportDateUntil').max = today;
    document.getElementById('exportDateFrom').max = today;

    // Закрытие модального окна при клике вне его
    document.addEventListener('click', function(event) {
        const modal = document.getElementById('exportModal');
        if (event.target === modal) {
            closeExportModal();
        }
    });

    // Обработчик для кнопки Enter в форме
    document.getElementById('exportForm').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            exportToExcel();
        }
    });
});


