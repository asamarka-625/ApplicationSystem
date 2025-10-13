const API_BASE_URL = 'http://localhost:8000/api/v1/request/create';

async function loadCreateInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/info`);
        const data = await response.json();
        const departament_data = data.departament;
        const request_type_data = data.request_type;

        const select_departament = document.getElementById('departamentSite');
        departament_data.forEach(departament => {
            const option = document.createElement('option');
            option.value = departament.code;
            option.textContent = departament.name;
            select_departament.appendChild(option);
        });

        const select_request_type = document.getElementById('requestType');
        request_type_data.forEach(request_type => {
            const option = document.createElement('option');
            option.value = request_type.id;
            option.textContent = request_type.name;
            select_request_type.appendChild(option);
        });

    } catch (error) {
        console.error('Ошибка загрузки информации:', error);
        showNotification('Ошибка загрузки информации', 'error');
    }
}

// Функции для индикации загрузки (заглушки)
function showLoading(show) {
    // Реализуйте отображение индикатора загрузки
    if (show) {
        console.log('Показываем загрузку...');
		
    } else {
        console.log('Скрываем загрузку...');
    }
}

function resetForm() {
    document.getElementById('requestForm').reset();
    document.querySelector('.emergency-section').style.display = 'none';
}

// Обработка отправки формы заявки
async function handleRequestSubmit(e) {
    e.preventDefault();
    
    // Явно находим форму по ID
    const form = document.getElementById('requestForm');
    if (!form) {
        console.error('Form with id "requestForm" not found');
        return;
    }

    const itemInputs = document.querySelectorAll('.request-item-input');
    const items = Array.from(itemInputs)
        .filter(input => input.value.trim() !== '')
        .map(input => (
            input.dataset.id ? Number(input.dataset.id) : null
        ));

    const formData = new FormData(form);

    const requestData = {
        items: items,
        description: formData.get('description') || '',
        request_type: Number(formData.get('requestTypeId')),
        departament: Number(formData.get('departamentId'))
    };

    try {
        const response = await fetch(`${API_BASE_URL}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (response.ok) {
            showNotification('Заявка успешно создана!');
            resetForm();
        } else {
            throw new Error('Ошибка создания заявки');
        }
    } catch (error) {
        console.error('Ошибка создания заявки:', error);
        showNotification('Ошибка создания заявки', 'error');
    }
}

document.addEventListener('DOMContentLoaded', function() {
	loadCreateInfo();
	
	// Получаем элементы
    const itemsContainer = document.getElementById('itemsContainer');
    const addItemBtn = document.getElementById('addItemBtn');

    // Функция для создания нового поля ввода
    function createItemField(value = '', itemId = '') {
        const wrapper = document.createElement('div');
        wrapper.className = 'item-input-wrapper';
        wrapper.innerHTML = `
            <div style="display: flex; align-items: center;">
                <input type="text" class="request-item-input" name="itemId"
                       placeholder="Выберите предметы" autocomplete="off"
                       value="${value}">
                <button type="button" class="btn-remove-item">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="suggestions-container"></div>
        `;

        const input = wrapper.querySelector('.request-item-input');
        const suggestions = wrapper.querySelector('.suggestions-container');
        const removeBtn = wrapper.querySelector('.btn-remove-item');

        if (itemId) {
            input.dataset.id = itemId;
        }

        // Обработчики для нового поля
        setupItemField(input, suggestions, removeBtn, wrapper);

        return wrapper;
    }

    // Функция настройки обработчиков для поля
    function setupItemField(input, suggestions, removeBtn, wrapper) {
        let searchTimeout;

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

    // Обработчик добавления нового поля
    addItemBtn.addEventListener('click', function() {
        const newField = createItemField();
        itemsContainer.appendChild(newField);
    });

    // Обновленная функция поиска
    async function searchItems(query, suggestionsContainer, input) {
        try {
            showLoading(true);
            const response = await fetch(`${API_BASE_URL}/item/?search=${encodeURIComponent(query)}`);

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

    // Обновленная функция отображения подсказок
    function displaySuggestions(items, suggestionsContainer, input) {
        if (!items || items.length === 0) {
            hideSuggestions(suggestionsContainer);
            return;
        }

        const suggestionsHTML = items.map(item => `
            <div class="suggestion-item" data-value="${item.id}">
                ${item.name} ${item.description}
            </div>
        `).join('');

        suggestionsContainer.innerHTML = suggestionsHTML;
        suggestionsContainer.style.display = 'block';
    }

    // Обновленная функция скрытия подсказок
    function hideSuggestions(suggestionsContainer) {
        suggestionsContainer.style.display = 'none';
    }

    // Обновленный обработчик клика вне поля
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.request-item-input') && !event.target.closest('.suggestion-item')) {
            document.querySelectorAll('.suggestions-container').forEach(hideSuggestions);
        }
    });

    // Инициализация первого поля
    const firstInput = document.querySelector('.request-item-input');
    const firstSuggestions = document.querySelector('.suggestions-container');
    const firstWrapper = document.querySelector('.item-input-wrapper');

    setupItemField(firstInput, firstSuggestions, null, firstWrapper);

	document.getElementById('sumbit_create').addEventListener('click', handleRequestSubmit);
});