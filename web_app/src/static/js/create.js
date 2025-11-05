const API_BASE_URL = '/api/v1/request/create';

// Переменная для хранения данных о типах заявок
let requestTypes = [];

async function loadCreateInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/info`);
        const data = await response.json();
        const request_type_data = data.request_type;
        requestTypes = request_type_data; // Сохраняем для использования в логике

        const select_request_type = document.getElementById('requestType');
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
        selectedType.name.toLowerCase().includes('техническое обслуживание')
    );
}

// Функция для обновления видимости полей в зависимости от типа заявки
function updateFormVisibility(requestTypeId) {
    const isMaintenance = isMaintenanceSupport(requestTypeId);

    const emergencyGroup = document.getElementById('emergencyGroup');
    const itemsGroup = document.getElementById('itemsGroup');
    const commentGroup = document.getElementById('commentGroup');
    const attachmentsSection = document.getElementById('attachmentsSection');

    if (isMaintenance) {
        // Скрываем поля для материально-технического обеспечения
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
    document.getElementById('isEmergency').checked = false;
    document.getElementById('requestDescription').value = '';
    document.getElementById('attachments').value = '';
}

// Функции для индикации загрузки
function showLoading(show) {
    if (show) {
        console.log('Показываем загрузку...');
    } else {
        console.log('Скрываем загрузку...');
    }
}

function resetForm() {
    const requestTypeSelectValue = document.getElementById('requestType').value;
    document.getElementById('requestForm').reset();

    // Сбрасываем поля предметов к одному
    const itemsContainer = document.getElementById('itemsContainer');
    const firstItemWrapper = itemsContainer.querySelector('.item-input-wrapper');
    itemsContainer.innerHTML = '';
    itemsContainer.appendChild(firstItemWrapper);

    // Скрываем кнопку удаления у первого элемента
    firstItemWrapper.querySelector('.btn-remove-item').style.display = 'none';

    // Обновляем видимость полей
    if (requestTypeSelectValue) {
        document.getElementById('requestType').value = requestTypeSelectValue;
        updateFormVisibility(requestTypeSelectValue);
    }
}

// Обработка отправки формы заявки
async function handleRequestSubmit(e) {
    e.preventDefault();

    const form = document.getElementById('requestForm');
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

        if (input.value.trim() !== '' && input.dataset.id) {
            // Проверяем количество
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
    const requestTypeId = Number(formData.get('requestTypeId'));
    const isMaintenance = isMaintenanceSupport(requestTypeId);

    formData.append('items', JSON.stringify(isMaintenance ? null : items));
    formData.append('is_emergency', isMaintenance ? (document.getElementById("isEmergency").checked || false) : false);
    formData.append('description', isMaintenance ? (document.getElementById('requestDescription').value || '') : '');
    formData.append('request_type', requestTypeId.toString());

    if (isMaintenance) {
        const fileInput = document.getElementById('attachments');
        if (fileInput.files.length > 5) {
            showNotification('Можно загрузить не более 5 файлов', 'error');
            return;
        }
    }

    console.log(formData);
    try {
        const submitButton = document.getElementById('sumbit_create');
        const originalText = submitButton.innerHTML;

        // Блокируем кнопку на время отправки
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Отправка...';

        const response = await fetch(`${API_BASE_URL}/`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            showNotification('Заявка успешно создана!');
            resetForm();
            window.location.href = '/requests';

        } else {
            throw new Error('Ошибка создания заявки');
        }

    } catch (error) {
        console.error('Ошибка создания заявки:', error);
        showNotification('Ошибка создания заявки', 'error');

    } finally {
        const submitButton = document.getElementById('sumbit_create');
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fas fa-paper-plane"></i> Отправить заявку';
    }
}

document.addEventListener('DOMContentLoaded', function() {
	loadCreateInfo();

	// Получаем элементы
    const itemsContainer = document.getElementById('itemsContainer');
    const addItemBtn = document.getElementById('addItemBtn');
    const requestTypeSelect = document.getElementById('requestType');

    // Обработчик изменения типа заявки
    requestTypeSelect.addEventListener('change', function() {
        updateFormVisibility(this.value);
    });

    // Функция для создания нового поля ввода предмета
    function createItemField(value = '', itemId = '', quantity = 1) {
        const wrapper = document.createElement('div');
        wrapper.className = 'item-input-wrapper';
        wrapper.innerHTML = `
            <div class="item-row">
                <div class="item-input-col">
                    <input type="text" class="request-item-input" name="itemId"
                           placeholder="Выберите предмет" autocomplete="off"
                           value="${value}">
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

        // Обработчики для нового поля
        setupItemField(input, suggestions, removeBtn, wrapper, quantityInput);

        return wrapper;
    }

    // Функция настройки обработчиков для поля предмета
    function setupItemField(input, suggestions, removeBtn, wrapper, quantityInput) {
        let searchTimeout;

        // Валидация количества
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

        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                // Не удаляем первое поле
                if (itemsContainer.children.length > 1) {
                    wrapper.remove();
                    // Обновляем видимость кнопок удаления
                    updateRemoveButtonsVisibility();
                }
            });
        }

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

    // Функция обновления видимости кнопок удаления
    function updateRemoveButtonsVisibility() {
        const removeButtons = itemsContainer.querySelectorAll('.btn-remove-item');
        const hasMultipleItems = itemsContainer.children.length > 1;

        removeButtons.forEach(btn => {
            btn.style.display = hasMultipleItems ? 'flex' : 'none';
        });
    }

    // Обработчик добавления нового поля
    addItemBtn.addEventListener('click', function() {
        const newField = createItemField();
        itemsContainer.appendChild(newField);
        updateRemoveButtonsVisibility();
    });

    // Функция поиска предметов
    async function searchItems(query, suggestionsContainer, input) {
        try {
            showLoading(true);
            const response = await fetch(`${API_BASE_URL}/item?search=${encodeURIComponent(query)}`);

            if (!response.ok) {
                throw new Error('Ошибка сети');
            }

            const results = await response.json();
            displaySuggestions(results, suggestionsContainer, input);

        } catch (error) {
            console.error('Ошибка поиска:', error);
            hideSuggestions(suggestionsContainer);
        } finally {
            showLoading(false);
        }
    }

    // Функция отображения подсказок
    function displaySuggestions(items, suggestionsContainer, input) {
        if (!items || items.length === 0) {
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
        suggestionsContainer.style.display = 'none';
    }

    // Обработчик клика вне поля
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.request-item-input') && !event.target.closest('.suggestion-item')) {
            document.querySelectorAll('.suggestions-container').forEach(hideSuggestions);
        }
    });

    // Инициализация первого поля
    const firstInput = document.querySelector('.request-item-input');
    const firstSuggestions = document.querySelector('.suggestions-container');
    const firstWrapper = document.querySelector('.item-input-wrapper');
    const firstQuantityInput = firstWrapper.querySelector('.item-quantity');
    const firstRemoveBtn = firstWrapper.querySelector('.btn-remove-item');

    setupItemField(firstInput, firstSuggestions, firstRemoveBtn, firstWrapper, firstQuantityInput);

    // Скрываем кнопку удаления у первого элемента
    firstRemoveBtn.style.display = 'none';

	// Обработчики отправки формы и сброса
	document.getElementById('sumbit_create').addEventListener('click', handleRequestSubmit);
    document.getElementById('reset_create').addEventListener('click', resetForm);
    initializeFileInput();
});

// Функция показа уведомлений
function showNotification(message, type = 'success') {
    // Реализуйте отображение уведомлений в соответствии с вашим проектом
    alert(`${type === 'success' ? '✓' : type === 'error' ? '✗' : '⚠'} ${message}`);
}

function initializeFileInput() {
    const fileInput = document.getElementById('attachments');
    const fileListContainer = document.createElement('div');
    fileListContainer.className = 'file-list';
    fileListContainer.style.marginTop = '10px';

    fileInput.parentNode.insertBefore(fileListContainer, fileInput.nextSibling);

    // Добавляем счетчик файлов
    const fileCounter = document.createElement('div');
    fileCounter.className = 'file-counter';
    fileCounter.style.marginBottom = '10px';
    fileCounter.style.fontSize = '0.9em';
    fileCounter.style.color = '#666';
    fileListContainer.parentNode.insertBefore(fileCounter, fileListContainer);

    // Храним текущие файлы
    let currentFiles = [];

    fileInput.addEventListener('change', function(e) {
        handleFileSelection(this, fileListContainer, fileCounter);
    });

    // Функция для обработки выбора файлов
    function handleFileSelection(input, container, counter) {
        const newFiles = Array.from(input.files);
        const maxFiles = 5;

        // Объединяем текущие файлы с новыми
        const allFiles = [...currentFiles, ...newFiles];

        // Убираем дубликаты по имени и размеру
        const uniqueFiles = allFiles.reduce((acc, file) => {
            const isDuplicate = acc.some(f =>
                f.name === file.name && f.size === file.size && f.type === file.type
            );
            if (!isDuplicate) {
                acc.push(file);
            }
            return acc;
        }, []);

        // Проверяем количество файлов
        if (uniqueFiles.length > maxFiles) {
            showNotification(`Можно загрузить не более ${maxFiles} файлов`, 'error');
            // Оставляем только первые 5 файлов
            currentFiles = uniqueFiles.slice(0, maxFiles);
        } else {
            currentFiles = uniqueFiles;
        }

        // Обновляем input files
        updateInputFiles(input, currentFiles);
        updateFileList(container, currentFiles, counter);
    }

    // Функция для обновления файлов в input
    function updateInputFiles(input, files) {
        const newFileList = new DataTransfer();
        files.forEach(file => newFileList.items.add(file));
        input.files = newFileList.files;
    }

    // Обновляем функцию updateFileList
    function updateFileList(container, files, counter) {
        container.innerHTML = '';

        // Обновляем счетчик
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
            fileItem.style.display = 'flex';
            fileItem.style.justifyContent = 'space-between';
            fileItem.style.alignItems = 'center';
            fileItem.style.padding = '8px';
            fileItem.style.borderBottom = '1px solid #eee';

            const fileInfo = document.createElement('div');
            fileInfo.style.display = 'flex';
            fileInfo.style.alignItems = 'center';
            fileInfo.style.gap = '8px';
            fileInfo.innerHTML = `
                <i class="fas ${getFileIcon(file.type)}" style="color: #6c757d;"></i>
                <span>${file.name}</span>
                <small style="color: #999;">(${formatFileSize(file.size)})</small>
            `;

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.innerHTML = '<i class="fas fa-times"></i>';
            removeBtn.className = 'btn-remove-file';
            removeBtn.style.background = 'none';
            removeBtn.style.border = 'none';
            removeBtn.style.color = '#dc3545';
            removeBtn.style.cursor = 'pointer';
            removeBtn.style.padding = '4px';
            removeBtn.style.borderRadius = '3px';

            removeBtn.addEventListener('click', function() {
                removeFile(i, container, counter);
            });

            fileItem.appendChild(fileInfo);
            fileItem.appendChild(removeBtn);
            fileList.appendChild(fileItem);
        }

        container.appendChild(fileList);
    }

    // Функция для удаления файла
    function removeFile(index, container, counter) {
        currentFiles.splice(index, 1);
        updateInputFiles(fileInput, currentFiles);
        updateFileList(container, currentFiles, counter);
    }

    // Функция для обновления счетчика файлов
    function updateFileCounter(counter, currentCount) {
        const maxFiles = 5;
        counter.textContent = `Выбрано файлов: ${currentCount}/${maxFiles}`;

        if (currentCount >= maxFiles) {
            counter.style.color = '#dc3545';
            counter.innerHTML += ' <i class="fas fa-exclamation-circle"></i> Лимит достигнут';
        } else {
            counter.style.color = '#28a745';
        }
    }

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

    // Инициализируем пустой список
    updateFileList(fileListContainer, currentFiles, fileCounter);
}