const API_URL = '/api/v1/request/view';
const API_BASE_URL = '/api/v1';

function getRegistrationNumberFromUrl() {
    const url = window.location.href;

    const parts = url.split('/');
    const registrationNumber = parts[parts.length - 1];

    return registrationNumber;
}

// Загружаем детали заявки
document.addEventListener('DOMContentLoaded', function() {
    const registrationNumber = getRegistrationNumberFromUrl()
    if (registrationNumber) {
        loadRequestDetails(registrationNumber);

    } else {
        showNotification('Номер заявки не указан', 'error');
    }

    // Элементы модального окна
    const userModal = document.getElementById('userModal');
    const userInfo = document.getElementById('userInfo');
    const closeModal = document.getElementById('closeModal');
    const closeBtn = document.querySelector('.close');

    const modal = document.getElementById('executorModal');
    const cancelBtn = document.getElementById('cancelExecutor');
    const assignBtn = document.getElementById('assignExecutor');

    // Закрытие модального окна
    closeBtn.onclick = function() {
        modal.style.display = 'none';
    }

    cancelBtn.onclick = function() {
        modal.style.display = 'none';
    }

    // Назначение исполнителя
    assignBtn.onclick = async function() {
        const executorId = document.getElementById('selectedExecutorId').value;

        if (!executorId) {
            showNotification('Выберите исполнителя', 'error');
            return;
        }

        try {
            const response = await fetch(``, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    executor_id: executorId
                })
            });

            if (response.ok) {
                showNotification('Исполнитель успешно назначен', 'success');
                modal.style.display = 'none';
                // Можно обновить интерфейс или перезагрузить данные
            } else {
                throw new Error('Ошибка назначения исполнителя');
            }

        } catch (error) {
            console.error('Ошибка:', error);
            showNotification('Ошибка назначения исполнителя', 'error');
        }
    };

    // Закрытие при клике вне модального окна
    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
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

    // Обработчики событий
    closeBtn.addEventListener('click', closeUserModal);
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

            const request = await response.json();
            displayRequestDetails(request);

        } catch (error) {
            console.error('Ошибка загрузки:', error);
            showNotification('Ошибка загрузки', 'error');
        }
    }

    function displayRequestDetails(request) {
        document.getElementById('requestDetails').style.display = 'block';

        // Заполняем данные
        document.getElementById('registrationNumber').textContent = request.registration_number;
        document.getElementById('regNumber').textContent = request.registration_number;
        document.getElementById('requestType').textContent = request.request_type.value;
        displayItems(request.items);

        document.getElementById('description').textContent = request.description;
        if (request.description_executor != null) {
            document.getElementById('description_executor').textContent = request.description_executor;
            document.getElementById('for_executor').style = '';
        }
        document.getElementById('department').textContent = request.department_name;
        document.getElementById('secretary_name').textContent = request.secretary.name;
        document.getElementById('judge_name').textContent = request.judge.name;
        document.getElementById('management_name').textContent = request.management.name ? request.management.name : 'Не назанчен';
        document.getElementById('executor_name').textContent = request.executor.name ? request.executor.name : 'Не назанчен';
        document.getElementById('createdAt').textContent = formatDate(request.created_at);
        document.getElementById('deadline').textContent = request.deadline ? formatDate(request.deadline) : 'Не задан';
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
        if (request.management.id) {
            management_button.classList.add('btn-info');
            management_button.addEventListener('click', () => {
                openUserModal(request.management.id);
            });
        } else {
            management_button.classList.add('btn-not-info');
        }

        const executor_button = document.getElementById('executor_name');
        if (request.executor.id) {
            executor_button.classList.add('btn-info');
            executor_button.addEventListener('click', () => {
                openUserModal(request.executor.id);
            });
        } else {
            executor_button.classList.add('btn-not-info');
        }

        if (request.attachments) {
            displayAttachments(request.attachments);
        } else {
            document.getElementById('attachments').innerHTML = '<span class="no-attachments">Файлы не прикреплены</span>';
        }

        displayRequestHistory(request.history);
    }

    function displayItems(items) {
        const itemsContainer = document.getElementById('items');

        if (!items || items.length === 0) {
            itemsContainer.innerHTML = 'Предметы не указаны';
            return;
        }

        const itemsList = document.createElement('div');
        itemsList.className = 'items-list';

        items.forEach(item => {
            const itemElement = document.createElement('div');
            itemElement.className = 'item-with-action';

            const itemName = document.createElement('span');
            itemName.className = 'item-name';
            itemName.textContent = `${item.name} [${item.quantity} шт.]`;

            const buttonsContainer = document.createElement('div');
            buttonsContainer.className = 'item-buttons';
            buttonsContainer.style.display = 'flex';
            buttonsContainer.style.gap = '8px';
            buttonsContainer.style.marginLeft = '10px';

            const assignButton = document.createElement('button');
            assignButton.className = 'assign-executor-btn';
            assignButton.innerHTML = '<i class="fas fa-user-plus"></i>';
            assignButton.title = 'Назначить исполнителя';
            assignButton.onclick = () => openExecutorModal(item.id, item.name);

            buttonsContainer.appendChild(assignButton);

            itemElement.appendChild(itemName);
            itemElement.appendChild(buttonsContainer);
            itemsList.appendChild(itemElement);
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
            link.download = attachment.file_path;

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

    function openExecutorModal(itemId, itemName) {
        currentItemId = itemId;

        // Обновляем заголовок модального окна
        document.querySelector('#executorModal h2').textContent = `Назначить исполнителя для: ${itemName}`;

        // Сбрасываем форму
        document.getElementById('selectedExecutor').style.display = 'none';
        document.getElementById('selectedExecutorId').value = '';
        document.getElementById('selectedExecutorName').textContent = '';

        // Загружаем исполнителей
        loadExecutors();

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
                    ${executor.position ? `<br><small>${executor.position}</small>` : ''}
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

    async function loadExecutors() {
        try {
            const response = await fetch(`${API_BASE_URL}/request/create/executors`);
            allExecutors = await response.json();

            // Инициализируем выбор исполнителей
            initializeExecutorSelection();

        } catch (error) {
            console.error('Ошибка загрузки исполнителей:', error);
            showNotification('Ошибка загрузки списка исполнителей', 'error');
        }
    }
});

