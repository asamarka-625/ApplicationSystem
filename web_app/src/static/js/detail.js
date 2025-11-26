const API_URL = '/api/v1/request/view';
const API_BASE_URL = '/api/v1';

let currentRejectId = null;
let currentEvent = null;

function getRegistrationNumberFromUrl() {
    const url = window.location.href;

    const parts = url.split('/');
    const registrationNumber = parts[parts.length - 1];

    return registrationNumber;
}

// Функция для открытия модального окна отклонения
function openRejectModal(e, id) {
    currentRejectId = id;
    currentEvent = e;

    const modal = document.getElementById('rejectModal');
    const textarea = document.getElementById('rejectReason');

    // Сброс формы
    textarea.value = '';
    modal.style.display = 'block';

    // Фокус на текстовом поле
    setTimeout(() => textarea.focus(), 100);
}

// Функция для закрытия модального окна
function closeRejectModal() {
    const modal = document.getElementById('rejectModal');
    modal.style.display = 'none';
    currentRejectId = null;
    currentEvent = null;
}

// Основная функция отклонения заявки
async function RejectRequest(reason) {
    try {
        const response = await fetch(`${API_BASE_URL}/request/reject/${currentRejectId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ comment: reason })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.status !== 'success') {
            throw new Error(data.message || 'Ошибка запроса');
        }

        // Скрываем кнопки (как в оригинальной функции)
        const buttonContainer = currentEvent.target.closest('div');
        const buttons = buttonContainer.querySelectorAll('a, button');

        buttons.forEach(button => {
            if (!button.classList.contains('btn-view-details')) {
                button.style.display = 'none';
            }
        });

        showNotification('Заявка отклонена', 'success');
        closeRejectModal();
        document.location.reload();
    } catch (error) {
        console.error('Ошибка при отклонении заявки:', error);
        showNotification('Ошибка при отклонении заявки', 'error');
    }
}

async function ConfirmRequest(e, id) {
    try {
        const response = await fetch(`${API_BASE_URL}/request/approve/${id}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            }
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

        showNotification('Заявка успешно утверждена', 'success');
        document.location.reload();

    } catch (error) {
        console.error('Ошибка утверждения заявки:', error);
        showNotification('Ошибка утверждения заявки', 'error');
    }
}

async function ExecuteRequest(e, id) {
    try {
        const response = await fetch(`${API_BASE_URL}/request/execute/${id}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            }
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

// Загружаем детали заявки
document.addEventListener('DOMContentLoaded', function() {
    const registrationNumber = getRegistrationNumberFromUrl()
    if (registrationNumber) {
        loadRequestDetails(registrationNumber);

    } else {
        showNotification('Номер заявки не указан', 'error');
    }

    const rejectModal = document.getElementById('rejectModal');
    const rejectForm = document.getElementById('rejectForm');
    const cancelReject = document.getElementById('cancelReject');
    const closeBtnReject = rejectModal.querySelector('.close');

    // Обработчик отправки формы
    rejectForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const reason = document.getElementById('rejectReason').value.trim();

        if (!reason) {
            showNotification('Пожалуйста, укажите причину отклонения', 'warning');
            return;
        }

        RejectRequest(reason);
    });

    // Обработчики закрытия модального окна
    cancelReject.addEventListener('click', closeRejectModal);
    closeBtnReject.addEventListener('click', closeRejectModal);

    // Элементы модального окна
    const userModal = document.getElementById('userModal');
    const userInfo = document.getElementById('userInfo');
    const closeModal = document.getElementById('closeModal');
    const closeBtn = document.querySelectorAll('.close');

    const modal = document.getElementById('executorModal');
    const cancelBtn = document.getElementById('cancelExecutor');
    const assignBtn = document.getElementById('assignExecutor');

    cancelBtn.onclick = function() {
        modal.style.display = 'none';
    }

    // Назначение исполнителя
    assignBtn.onclick = assignExecutor;

    // Закрытие при клике вне модального окна
    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }

        if (event.target === rejectModal) {
            closeRejectModal();
        }
    }

    // Функция для открытия модального окна с информацией о пользователе
    async function openUserModal(userId) {
        try {
            // Показываем индикатор загрузки
            userInfo.innerHTML = '<div class="loading">Загрузка...</div>';
            userModal.style.display = 'block';

            // Делаем запрос к API
            const response = await fetch(`${API_BASE_URL}/user/${userId}`);

            if (!response.ok) {
                throw new Error('Ошибка при получении данных пользователя');
            }

            const userData = await response.json();

            // Отображаем данные пользователя
            displayUserInfo(userData);

        } catch (error) {
            console.error('Ошибка:', error);
            userInfo.innerHTML = `<div class="error">Ошибка при загрузке данных: ${error.message}</div>`;
        }
    }

    // Функция для отображения информации о пользователе
    function displayUserInfo(user) {
        userInfo.innerHTML = `
            <div class="user-info-item">
                <span class="user-info-label">Имя:</span>
                <span class="user-info-value">${user.full_name || '—'}</span>
            </div>
            <div class="user-info-item">
                <span class="user-info-label">Роль:</span>
                <span class="user-info-value">${user.role || '—'}</span>
            </div>
            <div class="user-info-item">
                <span class="user-info-label">Номер телефона:</span>
                <span class="user-info-value">${user.phone || '—'}</span>
            </div>
            <div class="user-info-item">
                <span class="user-info-label">Email:</span>
                <span class="user-info-value">${user.email || '—'}</span>
            </div>
        `;
    }

    // Закрытие модального окна
    function closeUserModal() {
        userModal.style.display = 'none';
    }

    function closeModel() {
        modal.style.display = 'none';
    }

    // Обработчики событий
    closeBtn.forEach(btn => {
        btn.addEventListener('click', () => {
            closeUserModal();
            closeModel();
        });
    });
    closeModal.addEventListener('click', closeUserModal);

    // Закрытие при клике вне модального окна
    window.addEventListener('click', (event) => {
        if (event.target === userModal) {
            closeUserModal();
        }
    });

    async function loadRequestDetails(id) {
        try {
            const response = await fetch(`${API_URL}/detail/${id}`);
            if (!response.ok) {
                showNotification('Заявка не найдена', 'error');
            }

            const data = await response.json();
            displayRequestDetails(data);

        } catch (error) {
            console.error('Ошибка загрузки:', error);
            showNotification('Ошибка загрузки', 'error');
        }
    }

    function displayRequestDetails(data) {
        const request = data.details;
        const rights = data.rights;

        document.getElementById('requestDetails').style.display = 'block';
        const actionPanel = document.getElementById('actionPanel');
        const actionButtons = document.querySelector('.action-buttons-top');
        let buttonsHTML = '';

        if (rights.edit && request.rights.edit) {
            actionPanel.style.display = 'block';
            buttonsHTML += `
                <a class="btn btn-edit" href="/request/${request.registration_number}/edit">
                    <i class="fa-solid fa-pen-to-square"></i> Редактировать
                </a>`;
        }

        if (rights.approve && request.rights.approve) {
            actionPanel.style.display = 'block';
            buttonsHTML += `
                <button class="btn btn-approve" onclick="ConfirmRequest(event, '${request.registration_number}')">
                    <i class="fa-solid fa-thumbs-up"></i> Утвердить
                </button>`;
        }

        if (rights.redirect_management_department && request.rights.redirect_management_department) {
            actionPanel.style.display = 'block';
            buttonsHTML += `
                <a class="btn btn-redirect" href="/request/${request.registration_number}/redirect/management">
                    <i class="fa-solid fa-calendar-check"></i> Назначить сотрудника управления
                </a>`;
        }

        if ((rights.reject_after && request.rights.reject_after) || (rights.reject_before && request.rights.reject_before)) {
            actionPanel.style.display = 'block';
            buttonsHTML += `
                <button class="btn btn-reject" onclick="openRejectModal(event, '${request.registration_number}')">
                    <i class="fa-solid fa-xmark"></i> Отклонить
                </button>`;
        }

        if (rights.confirm_management_department && request.rights.confirm_management_department) {
            actionPanel.style.display = 'block';
            buttonsHTML += `
                <button class="btn btn-ready" onclick="ExecuteRequest(event, '${request.registration_number}')">
                    <i class="fa-solid fa-thumbs-up"></i> Подтвердить выполнение
                </button>`;
        }

        if (rights.confirm_management && request.rights.confirm_management) {
            actionPanel.style.display = 'block';
            buttonsHTML += `
                <button class="btn btn-ready" onclick="ExecuteRequest(event, '${request.registration_number}')">
                    <i class="fa-solid fa-thumbs-up"></i> Завершить
                </button>`;
        }

        actionButtons.innerHTML = buttonsHTML;

        // Заполняем данные
        document.getElementById('registrationNumber').textContent = request.registration_number;
        document.getElementById('humanRegistrationNumber').textContent = request.human_registration_number;
        document.getElementById('pdf_request').href = request.pdf_request;
        document.getElementById('regNumber').textContent = request.registration_number;
        document.getElementById('requestType').textContent = request.request_type.value;
        displayItems(request.items, request.rights, rights);

        document.getElementById('description').textContent = request.description;
        if (request.description_management_department != null) {
            document.getElementById('description_management_department').textContent = request.description_management_department;
            document.getElementById('for_description_management').style = '';
        }
        document.getElementById('department').textContent = request.department_name;
        document.getElementById('secretary_name').textContent = request.secretary.name;
        document.getElementById('judge_name').textContent = request.judge.name;
        document.getElementById('management_name').textContent = request.management ? request.management.name : 'Не назначен';
        document.getElementById('management_department_name').textContent = request.management_department ? request.management_department.name : 'Не назанчен';
        document.getElementById('createdAt').textContent = formatDate(request.created_at);
        document.getElementById('completedAt').textContent = request.completed_at ? formatDate(request.completed_at) : 'Не выполнена';
        document.getElementById('updatedAt').textContent = request.updated_at ? formatDate(request.updated_at) : 'Не обновлялась';

        // Статус
        const statusBadge = document.getElementById('statusBadge');
        statusBadge.textContent = request.status.value;
        statusBadge.className = `status-badge status-${request.status.name.toLowerCase()}`;

        // Срочность
        document.getElementById('emergency').innerHTML = request.is_emergency ?
            '<span class="emergency-badge">Аварийная</span>' : '<span>Обычная</span>';

        const secretary_button = document.getElementById('secretary_name');
        secretary_button.classList.add('btn-info');
        secretary_button.addEventListener('click', () => {
            openUserModal(request.secretary.id);
        });

        const judge_button = document.getElementById('judge_name');
        judge_button.classList.add('btn-info');
        judge_button.addEventListener('click', () => {
            openUserModal(request.judge.id);
        });

        const management_button = document.getElementById('management_name');
        if (request.management) {
            management_button.classList.add('btn-info');
            management_button.addEventListener('click', () => {
                openUserModal(request.management.id);
            });
        } else {
            management_button.classList.add('btn-not-info');
        }

        const management_department_button = document.getElementById('management_department_name');
        if (request.management_department) {
            management_department_button.classList.add('btn-info');
            management_department_button.addEventListener('click', () => {
                openUserModal(request.management_department.id);
            });
        } else {
            management_department_button.classList.add('btn-not-info');
        }

        if (request.attachments) {
            displayAttachments(request.attachments);
        } else {
            document.getElementById('attachments').innerHTML = '<span class="no-attachments">Файлы не прикреплены</span>';
        }

        displayRequestHistory(request.history);
    }

    function displayItems(items, request_rights, rights) {
        const itemsContainer = document.getElementById('items');

        if (!items || items.length === 0) {
            itemsContainer.innerHTML = '<div class="no-items">Предметы не указаны</div>';
            return;
        }

        const itemsList = document.createElement('div');
        itemsList.className = 'items-list';

        items.forEach(item => {
            const itemCard = document.createElement('div');
            itemCard.className = 'item-card';

            // Header с названием и действиями
            const itemHeader = document.createElement('div');
            itemHeader.className = 'item-header';

            const itemName = document.createElement('div');
            itemName.className = 'item-name';
            itemName.innerHTML = `
                ${item.name}
                <span class="badge quantity-badge">${item.quantity} шт.</span>
            `;

            const actionButtons = document.createElement('div');
            actionButtons.className = 'action-buttons';

            if (item.access && rights.redirect_executor && request_rights.redirect_executor) {
                const assignExecutorButton = document.createElement('button');
                assignExecutorButton.className = 'action-btn assign-executor-btn';
                assignExecutorButton.innerHTML = '<i class="fas fa-user-plus"></i>';
                assignExecutorButton.title = 'Назначить исполнителя';
                assignExecutorButton.onclick = () => openExecutorModal(item.id, `${item.name.substring(0, 15)}...`, true);
                actionButtons.appendChild(assignExecutorButton);
            }

            if (item.access && rights.redirect_org && request_rights.redirect_org) {
                const assignOrgButton = document.createElement('button');
                assignOrgButton.className = 'action-btn assign-org-btn';
                assignOrgButton.innerHTML = '<i class="fa-solid fa-users"></i>';
                assignOrgButton.title = 'Назначить организацию-исполнителя';
                assignOrgButton.onclick = () => openExecutorModal(item.id, `${item.name.substring(0, 15)}...`, false);
                actionButtons.appendChild(assignOrgButton);
            }

            itemHeader.appendChild(itemName);

            // Детали с исполнителями
            const itemDetails = document.createElement('div');
            itemDetails.className = 'item-details';

            const executorsSection = document.createElement('div');
            executorsSection.className = 'executors-section';

            // Исполнитель
            const executorInfo = document.createElement('div');
            executorInfo.className = 'executor-info';

            const executorBtn = document.createElement('button');
            executorBtn.className = `executor-btn ${item.executor ? 'assigned' : 'not-assigned'}`;
            executorBtn.innerHTML = `
                <i class="fas fa-user ${item.executor ? 'text-primary' : 'text-muted'}"></i>
                ${item.executor ? item.executor.name : 'Исполнитель не назначен'}
            `;

            if (item.executor) {
                executorBtn.addEventListener('click', () => openUserModal(item.executor.id));
            }
            executorInfo.appendChild(executorBtn);

            // Организация-исполнитель
            const orgInfo = document.createElement('div');
            orgInfo.className = 'executor-info organization';

            const orgBtn = document.createElement('button');
            orgBtn.className = `executor-btn ${item.executor_organization ? 'assigned' : 'not-assigned'}`;
            orgBtn.innerHTML = `
                <i class="fa-solid fa-building ${item.executor_organization ? 'text-success' : 'text-muted'}"></i>
                ${item.executor_organization ? item.executor_organization.name : 'Организация не назначена'}
            `;

            if (item.executor_organization) {
                orgBtn.addEventListener('click', () => openUserModal(item.executor_organization.id));
            }
            orgInfo.appendChild(orgBtn);

            executorsSection.appendChild(executorInfo);
            executorsSection.appendChild(orgInfo);
            itemDetails.appendChild(executorsSection);
            itemDetails.appendChild(actionButtons);
			
            const descriptionsSection = document.createElement('div');
            descriptionsSection.className = 'descriptions-section';
			
            const status_item = document.createElement('div');
            status_item.innerHTML = `
                <strong>Статус:</strong>
                ${item.status}
            `;
            descriptionsSection.appendChild(status_item);

            const deadline_executor = document.createElement('div');
            deadline_executor.innerHTML = `
                <strong>(Исполнитель) Срок выполнения:</strong>
                ${item.deadline_executor ? formatDate(item.deadline_executor, full=false) : 'не назначен'}
            `;
            descriptionsSection.appendChild(deadline_executor);

            if (item.description_executor) {
                const description = document.createElement('div');
                description.className = 'description';
                description.innerHTML = `<strong>Комментарий к исполнителю:</strong> ${item.description_executor}`;
                descriptionsSection.appendChild(description);
            }

            const deadline_organization = document.createElement('div');
            deadline_organization.innerHTML = `
                <strong>(Организация) Срок выполнения:</strong>
                ${item.deadline_organization ? formatDate(item.deadline_organization, full=false) : 'не назначен'}
            `;
            descriptionsSection.appendChild(deadline_organization);

            if (item.description_organization) {
                const description = document.createElement('div');
                description.className = 'description';
                description.innerHTML = `<strong>Комментарий к организации:</strong> ${item.description_organization}`;
                descriptionsSection.appendChild(description);
            }

            if (item.description_completed) {
                const description = document.createElement('div');
                description.className = 'description';
                description.innerHTML = `<strong>Комментарий от исполнителя:</strong> ${item.description_completed}`;
                descriptionsSection.appendChild(description);
            }

            // Сборка карточки
            itemCard.appendChild(itemHeader);
            itemCard.appendChild(itemDetails);
            if (descriptionsSection.children.length > 0) {
                itemCard.appendChild(descriptionsSection);
            }

            itemsList.appendChild(itemCard);
        });

        itemsContainer.innerHTML = '';
        itemsContainer.appendChild(itemsList);
    }

    function displayRequestHistory(history) {
        const historyBody = document.getElementById('historyBody');

        if (!history || history.length === 0) {
            historyBody.innerHTML = '<tr><td colspan="4" style="text-align: center;">История изменений отсутствует</td></tr>';
            return;
        }

        historyBody.innerHTML = history
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .map(item => `
            <tr>
                <td>${formatDate(item.created_at)}</td>
                <td>
                    <span class="status-badge status-${item.action.name.toLowerCase()}">
                        ${item.action.value}
                    </span>
                </td>
                <td>${(item.description || '—').replace(/\n/g, '<br>')}</td>
                <td>
                    ${item.user.name ?
                    `<button class="history btn-info" data-user-id=${item.user.id}>${item.user.name}</button>`
                    : 'Система'}
                </td>
            </tr>
        `).join('');

        historyBody.addEventListener('click', (event) => {
            if (event.target.classList.contains('history')) {
                openUserModal(event.target.dataset.userId);
            }
        });
    }

    function displayAttachments(attachments) {
        const attachmentsContainer = document.getElementById('attachments');

        if (!attachments || attachments.length === 0) {
            attachmentsContainer.innerHTML = '<span class="no-attachments">Файлы не прикреплены</span>';
            return;
        }

        const attachmentsList = document.createElement('div');
        attachmentsList.className = 'attachments-list';

        attachments.forEach(attachment => {
            const attachmentItem = document.createElement('div');
            attachmentItem.className = 'attachment-item';

            // Иконка в зависимости от типа файла
            const icon = document.createElement('i');
            icon.className = `fas ${getFileIcon(attachment.content_type)} attachment-icon`;

            // Ссылка для скачивания
            const link = document.createElement('a');
            link.className = 'attachment-link';
            link.textContent = `${attachment.file_name}.${attachment.content_type.split('/')[1]}`;
            link.target = '_blank';
            link.href = attachment.file_path;

            // Размер файла
            const size = document.createElement('span');
            size.className = 'attachment-size';
            size.textContent = formatFileSize(attachment.size);

            attachmentItem.appendChild(icon);
            attachmentItem.appendChild(link);
            attachmentItem.appendChild(size);
            attachmentsList.appendChild(attachmentItem);
        });

        attachmentsContainer.innerHTML = '';
        attachmentsContainer.appendChild(attachmentsList);
    }

    // Функция для получения иконки файла
    function getFileIcon(contentType) {
        if (contentType.startsWith('image/')) return 'fa-solid fa-image';
        if (contentType.startsWith('video/')) return 'fa-solid fa-file-video';
        return 'fa-file';
    }

    // Функция для форматирования размера файла
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function openExecutorModal(itemId, itemName, executor = true) {
        const modalName = document.querySelector('#executorModal h2');

        if (executor) {
            modalName.textContent = `Назначить исполнителя для: ${itemName}`;
        } else {
            modalName.textContent = `Назначить организацию-исполнителя для: ${itemName}`;
        }

        modalName.dataset.itemId = itemId;
        modalName.dataset.executor = executor;

        // Сбрасываем форму
        document.getElementById('selectedExecutor').style.display = 'none';
        document.getElementById('selectedExecutorId').value = '';
        document.getElementById('selectedExecutorName').textContent = '';

        // Сбрасываем дополнительные поля
        document.getElementById('executionComment').value = '';
        const deadlineInput = document.getElementById('executionDeadline');
        const defaultDate = new Date();
        defaultDate.setDate(defaultDate.getDate() + 20);

        // Форматируем дату в формат YYYY-MM-DD для input type="date"
        const formattedDate = defaultDate.toISOString().split('T')[0];
        deadlineInput.value = formattedDate;

        // Загружаем исполнителей
        loadExecutors(executor);

        // Показываем модальное окно
        document.getElementById('executorModal').style.display = 'block';
    }

    // Функция инициализации выбора исполнителей
    function initializeExecutorSelection() {
        const suggestionsContainer = document.getElementById('executorSuggestions');

        // Отображаем всех исполнителей сразу
        displayExecutorSuggestions(allExecutors);

        function displayExecutorSuggestions(executors) {
            if (executors.length === 0) {
                suggestionsContainer.innerHTML = '<div class="executor-suggestion-item">Исполнители не найдены</div>';
                suggestionsContainer.style.display = 'block';
                return;
            }

            const suggestionsHTML = executors.map(executor => `
                <div class="executor-suggestion-item" data-executor-id="${executor.id}">
                    <strong>${executor.full_name}</strong>
                    ${executor.position ? `<br><small>${executor.position}</small>` : `<br><small>${executor.name}</small>`}
                </div>
            `).join('');

            suggestionsContainer.innerHTML = suggestionsHTML;
            suggestionsContainer.style.display = 'block';

            // Добавляем обработчики клика
            suggestionsContainer.querySelectorAll('.executor-suggestion-item').forEach(item => {
                item.addEventListener('click', function() {
                    const executorId = this.getAttribute('data-executor-id');
                    const executorName = this.querySelector('strong').textContent;

                    selectExecutor(executorId, executorName);
                    hideSuggestions();
                });
            });
        }

        function hideSuggestions() {
            suggestionsContainer.style.display = 'none';
        }

        function selectExecutor(executorId, executorName) {
            document.getElementById('selectedExecutorId').value = executorId;
            document.getElementById('selectedExecutorName').textContent = executorName;
            document.getElementById('selectedExecutor').style.display = 'block';
        }
    }

    async function loadExecutors(executor) {
        try {
            let response;
            if (executor) {
                response = await fetch(`${API_BASE_URL}/request/create/executors`);
            } else {
                response = await fetch(`${API_BASE_URL}/request/create/organizations`);
            }

            allExecutors = await response.json();

            // Инициализируем выбор исполнителей
            initializeExecutorSelection();

        } catch (error) {
            console.error('Ошибка загрузки исполнителей:', error);
            showNotification('Ошибка загрузки списка исполнителей', 'error');
        }
    }

    function assignExecutor() {
        const executorId = document.getElementById('selectedExecutorId').value;
        const modalName = document.querySelector('#executorModal h2');
        const itemId = modalName.dataset.itemId;
        const executor_flag = modalName.dataset.executor === 'true';
        const comment = document.getElementById('executionComment').value;
        const deadline = document.getElementById('executionDeadline').value;

        if (!executorId) {
            showNotification('Пожалуйста, выберите исполнителя', 'error');
            return;
        }

        if (!deadline) {
            showNotification('Пожалуйста, укажите корректный срок исполнения', 'error');
            return;
        }

        const assignmentData = {
            item_id: itemId,
            user_role_id: executorId,
            description: comment,
            deadline: deadline,
        };

        const registrationNumber = getRegistrationNumberFromUrl();
        let url;
        if (executor_flag) {
            url = `${API_BASE_URL}/request/redirect/executor/${registrationNumber}`;
        } else {
            url = `${API_BASE_URL}/request/redirect/organization/${registrationNumber}`;
        }

        // Отправка данных на сервер
        fetch(url, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(assignmentData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status == 'success') {
                showNotification('Исполнитель успешно назначен', 'success');
                window.location.reload();
            } else {
                showNotification('Ошибка при назначении исполнителя: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showNotification('Ошибка при назначении исполнителя', 'error');
        });
    }
});

