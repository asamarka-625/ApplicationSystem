const API_URL = '/api/v1/request/create';
const API_BASE_URL = '/api/v1/request';

// Переменная для хранения данных о типах заявок
let requestTypes = [];
let currentRequestData = null;

function getRegistrationNumberFromUrl() {
    const url = window.location.href;
    const parts = url.split('/');
    const registrationNumber = parts[parts.length - 2];
    return registrationNumber;
}

// Функция проверки существования элемента
function getElementSafe(id) {
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`Элемент с id "${id}" не найден`);
    }
    return element;
}

async function loadCreateInfo() {
    try {
        const response = await fetch(`${API_URL}/info`);
        const data = await response.json();
        const request_type_data = data.request_type;
        requestTypes = request_type_data;

        const select_request_type = getElementSafe('requestType');
        if (!select_request_type) return;

        select_request_type.innerHTML = '<option value="">Выберите тип заявки</option>';
        request_type_data.forEach(request_type => {
            const option = document.createElement('option');
            option.value = request_type.id;
            option.textContent = request_type.name;
            option.dataset.category = request_type.category || '';
            select_request_type.appendChild(option);
        });

    } catch (error) {
        console.error('Ошибка загрузки информации:', error);
        showNotification('Ошибка загрузки информации', 'error');
    }
}

// Функция для проверки, является ли тип заявки "Материально-техническое обеспечение"
function isMaintenanceSupport(requestTypeId) {
    const selectedType = requestTypes.find(type => type.id == requestTypeId);
    return selectedType && (
        selectedType.name.toLowerCase().includes('услуги')
    );
}

// Функция для обновления видимости полей в зависимости от типа заявки
function updateFormVisibility(requestTypeId) {
    const emergencyGroup = getElementSafe('emergencyGroup');
    const itemsGroup = getElementSafe('itemsGroup');
    const commentGroup = getElementSafe('commentGroup');
    const attachmentsSection = getElementSafe('attachmentsSection');

    if (!emergencyGroup || !itemsGroup || !commentGroup || !attachmentsSection) return;

    const isMaintenance = isMaintenanceSupport(requestTypeId);

    if (isMaintenance) {
        emergencyGroup.classList.remove('hidden-section');
        itemsGroup.classList.add('hidden-section');
        commentGroup.classList.remove('hidden-section');
        attachmentsSection.classList.remove('hidden-section');
    } else {
        emergencyGroup.classList.add('hidden-section');
        itemsGroup.classList.remove('hidden-section');
        commentGroup.classList.add('hidden-section');
        attachmentsSection.classList.add('hidden-section');
    }

    // Сбрасываем значения скрытых полей
    const isEmergencyCheckbox = getElementSafe('isEmergency');
    const requestDescription = getElementSafe('requestDescription');
    const attachments = getElementSafe('attachments');

    if (isEmergencyCheckbox) isEmergencyCheckbox.checked = false;
    if (requestDescription) requestDescription.value = '';
    if (attachments) attachments.value = '';
}

// Функция загрузки данных заявки
async function loadRequestData() {
    try {
        const registrationNumber = getRegistrationNumberFromUrl();
        if (!registrationNumber) {
            console.error('Не удалось получить номер заявки из URL');
            return null;
        }

        const response = await fetch(`${API_BASE_URL}/view/detail/${registrationNumber}`);

        if (!response.ok) {
            throw new Error(`Ошибка загрузки данных заявки: ${response.status}`);
        }

        const data = await response.json();
        currentRequestData = data.details;
        return data.details;;

    } catch (error) {
        console.error('Ошибка загрузки данных заявки:', error);
        showNotification('Ошибка загрузки данных заявки', 'error');
        return null;
    }
}

// Функция заполнения формы данными заявки
function populateFormWithData(requestData) {
    if (!requestData) return;

    // Заполняем тип заявки
    const requestTypeSelect = getElementSafe('requestType');
    if (requestTypeSelect && requestData.request_type) {
        const requestTypeName = requestData.request_type.value;

        // Ищем option с соответствующим названием
        let foundOption = null;
        for (let option of requestTypeSelect.options) {
            if (option.textContent.toLowerCase().trim() === requestTypeName.toLowerCase().trim()) {
                foundOption = option;
                break;
            }
        }

        if (foundOption) {
            requestTypeSelect.value = foundOption.value;
            // Обновляем видимость полей
            updateFormVisibility(foundOption.value);
        } else {
            console.warn('Тип заявки не найден в списке:', requestTypeName);
        }
    }

    // Заполняем чекбокс аварийности
    const isEmergencyCheckbox = getElementSafe('isEmergency');
    if (isEmergencyCheckbox && requestData.is_emergency !== undefined) {
        isEmergencyCheckbox.checked = requestData.is_emergency;
    }

    // Заполняем описание
    const requestDescription = getElementSafe('requestDescription');
    if (requestDescription && requestData.description) {
        requestDescription.value = requestData.description;
    }

    // Заполняем предметы
    if (requestData.items && requestData.items.length > 0) {
        populateItems(requestData.items);
    }

    // Загружаем прикрепленные файлы (если есть)
    if (requestData.attachments && requestData.attachments.length > 0) {
        populateAttachments(requestData.attachments);
    }
}

// Функция заполнения предметов
function populateItems(items) {
    const itemsContainer = getElementSafe('itemsContainer');
    if (!itemsContainer) return;

    itemsContainer.innerHTML = '';

    items.forEach((item, index) => {
        const itemField = createItemField(
            `${item.name}${item.description ? ` - ${item.description}` : ''}`,
            item.id,
            item.quantity || 1
        );
        itemsContainer.appendChild(itemField);
    });

    updateRemoveButtonsVisibility();
}

// Функция заполнения информации о файлах
function populateAttachments(attachments) {
    displayExistingAttachments(attachments);
}

// Функция отображения существующих прикрепленных файлов
function displayExistingAttachments(attachments) {
    const fileListContainer = document.querySelector('.file-list');
    const fileCounter = document.querySelector('.file-counter');

    if (!fileListContainer || !fileCounter) {
        console.warn('Контейнеры для файлов не найдены');
        return;
    }

    if (attachments.length === 0) {
        fileListContainer.innerHTML = '<small>Нет прикрепленных файлов</small>';
        updateFileCounter(fileCounter, 0);
        return;
    }

    const fileList = document.createElement('div');
    fileList.className = 'file-list-items';

    attachments.forEach(attachment => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item existing-file';
        fileItem.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px;
            border-bottom: 1px solid #eee;
            background-color: #f8f9fa;
        `;

        const fileInfo = document.createElement('div');
        fileInfo.style.cssText = `
            display: flex;
            align-items: center;
            gap: 8px;
        `;

        const fileName = attachment.file_name || 'Файл';
        const fileSize = attachment.file_size ? `(${formatFileSize(attachment.file_size)})` : '';

        fileInfo.innerHTML = `
            <i class="fas ${getFileIcon(attachment.file_type || '')}" style="color: #6c757d;"></i>
            <a href="${attachment.file_url || '#'}" target="_blank" style="text-decoration: none; color: #007bff;">
                ${fileName}
            </a>
            <small style="color: #999;">${fileSize}</small>
        `;

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.innerHTML = '<i class="fas fa-times"></i>';
        removeBtn.className = 'btn-remove-existing-file';
        removeBtn.style.cssText = `
            background: none;
            border: none;
            color: #dc3545;
            cursor: pointer;
            padding: 4px;
            border-radius: 3px;
        `;
        removeBtn.title = 'Удалить файл';

        removeBtn.addEventListener('click', function() {
            removeExistingAttachment(attachment.file_name, fileItem);
        });

        fileItem.appendChild(fileInfo);
        fileItem.appendChild(removeBtn);
        fileList.appendChild(fileItem);
    });

    fileListContainer.innerHTML = '';
    fileListContainer.appendChild(fileList);
    updateFileCounter(fileCounter, attachments.length);
}

// Функция удаления существующего файла
async function removeExistingAttachment(attachmentId, fileElement) {
    if (!confirm('Вы уверены, что хотите удалить этот файл?')) {
        return;
    }

    const registrationNumber = getRegistrationNumberFromUrl();

    try {
        const response = await fetch(`${API_BASE_URL}/attachment/${registrationNumber}/${attachmentId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            fileElement.remove();
            showNotification('Файл успешно удален', 'success');
            const fileCounter = document.querySelector('.file-counter');
            const remainingFiles = document.querySelectorAll('.existing-file').length;
            updateFileCounter(fileCounter, remainingFiles);
        } else {
            throw new Error('Ошибка удаления файла');
        }
    } catch (error) {
        console.error('Ошибка удаления файла:', error);
        showNotification('Ошибка удаления файла', 'error');
    }
}

// Функция создания поля предмета
function createItemField(value = '', itemId = '', quantity = 1) {
    const wrapper = document.createElement('div');
    wrapper.className = 'item-input-wrapper';
    wrapper.innerHTML = `
        <div class="item-row">
            <div class="item-input-col">
                <input type="text" class="request-item-input" name="itemId"
                       placeholder="Выберите предмет" autocomplete="off"
                       value="${value.replace(/"/g, '&quot;')}">
                <div class="suggestions-container"></div>
            </div>
            <div class="item-quantity-col">
                <input type="number" class="item-quantity" name="itemQuantity"
                       value="${quantity}" min="1" required placeholder="Кол-во">
            </div>
            <div class="item-actions-col">
                <button type="button" class="btn-remove-item">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;

    const input = wrapper.querySelector('.request-item-input');
    const suggestions = wrapper.querySelector('.suggestions-container');
    const removeBtn = wrapper.querySelector('.btn-remove-item');
    const quantityInput = wrapper.querySelector('.item-quantity');

    if (itemId) {
        input.dataset.id = itemId;
    }

    setupItemField(input, suggestions, removeBtn, wrapper, quantityInput);
    return wrapper;
}

// Функция настройки обработчиков для поля предмета
function setupItemField(input, suggestions, removeBtn, wrapper, quantityInput) {
    let searchTimeout;

    // Валидация количества
    if (quantityInput) {
        quantityInput.addEventListener('change', function() {
            if (this.value < 1) {
                this.value = 1;
                showNotification('Количество не может быть меньше 1', 'warning');
            }
        });

        quantityInput.addEventListener('input', function() {
            if (this.value < 1) {
                this.value = 1;
            }
        });
    }

    if (input && suggestions) {
        input.addEventListener('input', function(event) {
            const searchTerm = event.target.value.trim();
            clearTimeout(searchTimeout);

            if (searchTerm.length > 2) {
                searchTimeout = setTimeout(() => {
                    searchItems(searchTerm, suggestions, input);
                }, 300);
            } else {
                hideSuggestions(suggestions);
            }
        });

        // Обработчик клика по подсказке
        suggestions.addEventListener('click', function(event) {
            if (event.target.classList.contains('suggestion-item')) {
                const value = event.target.getAttribute('data-value');
                const name = event.target.textContent.trim();
                input.value = name;
                input.dataset.id = value;
                hideSuggestions(suggestions);
            }
        });

        // Скрытие подсказок
        input.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                hideSuggestions(suggestions);
            }
        });
    }

    if (removeBtn) {
        removeBtn.addEventListener('click', function() {
            const itemsContainer = getElementSafe('itemsContainer');
            if (itemsContainer && itemsContainer.children.length > 1) {
                wrapper.remove();
                updateRemoveButtonsVisibility();
            }
        });
    }
}

// Функция обновления видимости кнопок удаления
function updateRemoveButtonsVisibility() {
    const itemsContainer = getElementSafe('itemsContainer');
    if (!itemsContainer) return;

    const removeButtons = itemsContainer.querySelectorAll('.btn-remove-item');
    const hasMultipleItems = itemsContainer.children.length > 1;

    removeButtons.forEach(btn => {
        if (btn) {
            btn.style.display = hasMultipleItems ? 'flex' : 'none';
        }
    });
}

// Функция сброса формы
function resetForm() {
    if (currentRequestData) {
        populateFormWithData(currentRequestData);
    } else {
        const requestTypeSelect = getElementSafe('requestType');
        const requestForm = getElementSafe('requestForm');
        const itemsContainer = getElementSafe('itemsContainer');

        if (requestForm) requestForm.reset();

        if (itemsContainer) {
            const firstItemWrapper = itemsContainer.querySelector('.item-input-wrapper');
            if (firstItemWrapper) {
                itemsContainer.innerHTML = '';
                itemsContainer.appendChild(firstItemWrapper);
                const firstRemoveBtn = firstItemWrapper.querySelector('.btn-remove-item');
                if (firstRemoveBtn) firstRemoveBtn.style.display = 'none';
            }
        }

        if (requestTypeSelect && requestTypeSelect.value) {
            updateFormVisibility(requestTypeSelect.value);
        }
    }
}

// Обработка отправки формы заявки
async function handleRequestSubmit(e) {
    e.preventDefault();

    const form = getElementSafe('requestForm');
    if (!form) {
        console.error('Form with id "requestForm" not found');
        return;
    }

    // Собираем данные о предметах с количествами
    const items = [];
    const itemInputs = document.querySelectorAll('.item-input-wrapper');

    for (const wrapper of itemInputs) {
        const input = wrapper.querySelector('.request-item-input');
        const quantityInput = wrapper.querySelector('.item-quantity');

        if (input && input.value.trim() !== '' && input.dataset.id && quantityInput) {
            const quantity = parseInt(quantityInput.value);
            if (quantity < 1) {
                showNotification('Количество предметов не может быть меньше 1', 'error');
                quantityInput.focus();
                return;
            }

            items.push({
                id: Number(input.dataset.id),
                quantity: quantity
            });
        }
    }

    const formData = new FormData(form);
    const requestTypeId = Number(formData.get('requestTypeId') || 0);
    const isMaintenance = isMaintenanceSupport(requestTypeId);

    formData.append('items', JSON.stringify(isMaintenance ? null : items));

    const isEmergencyCheckbox = getElementSafe('isEmergency');
    formData.append('is_emergency', isMaintenance ? (isEmergencyCheckbox?.checked || false) : false);

    const requestDescription = getElementSafe('requestDescription');
    formData.append('description', isMaintenance ? (requestDescription?.value || '') : '');

    formData.append('request_type', requestTypeId.toString());

    if (isMaintenance) {
        const fileInput = getElementSafe('attachments');
        const existingFiles = document.querySelectorAll('.existing-file').length;
        if (fileInput && fileInput.files.length + existingFiles > 5) {
            showNotification('Можно загрузить не более 5 файлов всего', 'error');
            return;
        }
    }

    try {
        const submitButton = getElementSafe('sumbit_create');
        const registrationNumber = getRegistrationNumberFromUrl();

        if (!submitButton || !registrationNumber) {
            throw new Error('Не удалось найти необходимые элементы');
        }

        // Блокируем кнопку на время отправки
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Сохранение...';

        const response = await fetch(`${API_BASE_URL}/edit/${registrationNumber}`, {
            method: 'PATCH',
            body: formData
        });

        if (response.ok) {
            showNotification('Заявка успешно обновлена!');
            window.location.href = `/request/${registrationNumber}`;
        } else {
            const errorText = await response.text();
            throw new Error(errorText || 'Ошибка обновления заявки');
        }

    } catch (error) {
        console.error('Ошибка обновления заявки:', error);
        showNotification(error.message || 'Ошибка обновления заявки', 'error');
    } finally {
        const submitButton = getElementSafe('sumbit_create');
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="fas fa-save"></i> Сохранить изменения';
        }
    }
}

// Функция поиска предметов
async function searchItems(query, suggestionsContainer, input) {
    try {
        const response = await fetch(`${API_URL}/item?search=${encodeURIComponent(query)}`);

        if (!response.ok) {
            throw new Error('Ошибка сети');
        }

        const results = await response.json();
        displaySuggestions(results, suggestionsContainer, input);

    } catch (error) {
        console.error('Ошибка поиска:', error);
        hideSuggestions(suggestionsContainer);
    }
}

// Функция отображения подсказок
function displaySuggestions(items, suggestionsContainer, input) {
    if (!suggestionsContainer || !items || items.length === 0) {
        hideSuggestions(suggestionsContainer);
        return;
    }

    const suggestionsHTML = items.map(item => `
        <div class="suggestion-item" data-value="${item.id}">
            ${item.name} ${item.description ? `- ${item.description}` : ''}
        </div>
    `).join('');

    suggestionsContainer.innerHTML = suggestionsHTML;
    suggestionsContainer.style.display = 'block';
}

// Функция скрытия подсказок
function hideSuggestions(suggestionsContainer) {
    if (suggestionsContainer) {
        suggestionsContainer.style.display = 'none';
    }
}

// Вспомогательные функции для файлов
function getFileIcon(fileType) {
    if (fileType.startsWith('image/')) return 'fa-file-image';
    if (fileType.startsWith('video/')) return 'fa-file-video';
    if (fileType === 'application/pdf') return 'fa-file-pdf';
    if (fileType.includes('word') || fileType.includes('document')) return 'fa-file-word';
    if (fileType.includes('excel') || fileType.includes('spreadsheet')) return 'fa-file-excel';
    if (fileType.includes('zip') || fileType.includes('rar') || fileType.includes('archive')) return 'fa-file-archive';
    if (fileType.includes('text')) return 'fa-file-alt';
    return 'fa-file';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function updateFileCounter(counter, currentCount) {
    if (!counter) return;

    const maxFiles = 5;
    counter.textContent = `Выбрано файлов: ${currentCount}/${maxFiles}`;

    if (currentCount >= maxFiles) {
        counter.style.color = '#dc3545';
        counter.innerHTML += ' <i class="fas fa-exclamation-circle"></i> Лимит достигнут';
    } else {
        counter.style.color = '#28a745';
    }
}

// Функция показа уведомлений
function showNotification(message, type = 'success') {
    // Временная реализация - замените на вашу систему уведомлений
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        z-index: 10000;
        font-family: Arial, sans-serif;
        max-width: 300px;
    `;

    if (type === 'success') {
        notification.style.backgroundColor = '#28a745';
    } else if (type === 'error') {
        notification.style.backgroundColor = '#dc3545';
    } else {
        notification.style.backgroundColor = '#ffc107';
        notification.style.color = '#000';
    }

    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Основная инициализация
document.addEventListener('DOMContentLoaded', async function() {
    console.log('DOM загружен, начинаем инициализацию...');

    // Ждем загрузки информации о типах заявок
    await loadCreateInfo();

    // Затем загружаем данные заявки
    const requestData = await loadRequestData();
    if (requestData) {
        populateFormWithData(requestData);
    } else {
        console.log('Не удалось загрузить данные заявки');
    }

    // Инициализируем остальные компоненты
    initializeFileInput();
    setupEventListeners();
});

function setupEventListeners() {
    const requestTypeSelect = getElementSafe('requestType');
    const addItemBtn = getElementSafe('addItemBtn');
    const submitBtn = getElementSafe('sumbit_create');
    const resetBtn = getElementSafe('reset_create');

    if (requestTypeSelect) {
        requestTypeSelect.addEventListener('change', function() {
            updateFormVisibility(this.value);
        });
    }

    if (addItemBtn) {
        addItemBtn.addEventListener('click', function() {
            const itemsContainer = getElementSafe('itemsContainer');
            if (itemsContainer) {
                const newField = createItemField();
                itemsContainer.appendChild(newField);
                updateRemoveButtonsVisibility();
            }
        });
    }

    if (submitBtn) {
        submitBtn.addEventListener('click', handleRequestSubmit);
    }

    if (resetBtn) {
        resetBtn.addEventListener('click', resetForm);
    }

    // Обработчик клика вне поля для скрытия подсказок
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.request-item-input') && !event.target.closest('.suggestion-item')) {
            document.querySelectorAll('.suggestions-container').forEach(container => {
                hideSuggestions(container);
            });
        }
    });
}

// Функция initializeFileInput остается без изменений из вашего исходного кода
function initializeFileInput() {
    const fileInput = getElementSafe('attachments');
    if (!fileInput) {
        console.warn('File input not found');
        return;
    }

    const fileListContainer = document.createElement('div');
    fileListContainer.className = 'file-list';
    fileListContainer.style.marginTop = '10px';

    fileInput.parentNode.insertBefore(fileListContainer, fileInput.nextSibling);

    const fileCounter = document.createElement('div');
    fileCounter.className = 'file-counter';
    fileCounter.style.cssText = 'margin-bottom: 10px; font-size: 0.9em; color: #666;';
    fileListContainer.parentNode.insertBefore(fileCounter, fileListContainer);

    let currentFiles = [];

    fileInput.addEventListener('change', function(e) {
        handleFileSelection(this, fileListContainer, fileCounter);
    });

    function handleFileSelection(input, container, counter) {
        const newFiles = Array.from(input.files);
        const maxFiles = 5;

        const allFiles = [...currentFiles, ...newFiles];
        const uniqueFiles = allFiles.reduce((acc, file) => {
            const isDuplicate = acc.some(f =>
                f.name === file.name && f.size === file.size && f.type === file.type
            );
            if (!isDuplicate) {
                acc.push(file);
            }
            return acc;
        }, []);

        if (uniqueFiles.length > maxFiles) {
            showNotification(`Можно загрузить не более ${maxFiles} файлов`, 'error');
            currentFiles = uniqueFiles.slice(0, maxFiles);
        } else {
            currentFiles = uniqueFiles;
        }

        updateInputFiles(input, currentFiles);
        updateFileList(container, currentFiles, counter);
    }

    function updateInputFiles(input, files) {
        const newFileList = new DataTransfer();
        files.forEach(file => newFileList.items.add(file));
        input.files = newFileList.files;
    }

    function updateFileList(container, files, counter) {
        if (!container) return;

        container.innerHTML = '';
        updateFileCounter(counter, files.length);

        if (files.length === 0) {
            container.innerHTML = '<small>Файлы не выбраны</small>';
            return;
        }

        const fileList = document.createElement('div');
        fileList.className = 'file-list-items';

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.style.cssText = `
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px;
                border-bottom: 1px solid #eee;
            `;

            const fileInfo = document.createElement('div');
            fileInfo.style.cssText = `
                display: flex;
                align-items: center;
                gap: 8px;
            `;
            fileInfo.innerHTML = `
                <i class="fas ${getFileIcon(file.type)}" style="color: #6c757d;"></i>
                <span>${file.name}</span>
                <small style="color: #999;">(${formatFileSize(file.size)})</small>
            `;

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.innerHTML = '<i class="fas fa-times"></i>';
            removeBtn.className = 'btn-remove-file';
            removeBtn.style.cssText = `
                background: none;
                border: none;
                color: #dc3545;
                cursor: pointer;
                padding: 4px;
                border-radius: 3px;
            `;

            removeBtn.addEventListener('click', function() {
                removeFile(i, container, counter);
            });

            fileItem.appendChild(fileInfo);
            fileItem.appendChild(removeBtn);
            fileList.appendChild(fileItem);
        }

        container.appendChild(fileList);
    }

    function removeFile(index, container, counter) {
        currentFiles.splice(index, 1);
        updateInputFiles(fileInput, currentFiles);
        updateFileList(container, currentFiles, counter);
    }

    // Инициализируем пустой список
    updateFileList(fileListContainer, currentFiles, fileCounter);
}