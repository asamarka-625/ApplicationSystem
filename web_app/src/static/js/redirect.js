const API_URL = '/api/v1/request/create';
const API_BASE_URL = '/api/v1/request';

function getRegistrationNumberFromUrl() {
    const url = window.location.href;

    const parts = url.split('/');
    const registrationNumber = parts[parts.length - 2];

    return registrationNumber;
}

async function submitExecutorAssignment(registrationNumber, executorId, executorComment) {
    try {
        console.log(executorId, executorComment);
        const response = await fetch(`${API_BASE_URL}/redirect/${registrationNumber}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                executor: executorId,
                description: executorComment || ''
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;

    } catch (error) {
        console.error('Ошибка назначения исполнителя:', error);
        throw error;
    }
}

// Функция поиска исполнителей
async function searchExecutors(query, suggestionsContainer, input) {
    try {
        if (query.length < 2) {
            hideSuggestions(suggestionsContainer);
            return;
        }

        showLoading(true);
        const response = await fetch(`${API_URL}/executor/?search=${encodeURIComponent(query)}`);

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
function displaySuggestions(executors, suggestionsContainer, input) {
    if (!executors || executors.length === 0) {
        suggestionsContainer.innerHTML = '<div class="suggestion-item">Исполнители не найдены</div>';
        suggestionsContainer.style.display = 'block';
        return;
    }

    const suggestionsHTML = executors.map(executor => `
        <div class="suggestion-item" data-executor-id="${executor.id}">
            <strong>${executor.full_name || executor.name}</strong>
            ${executor.position ? `<br><small>${executor.position}</small>` : ''}
            ${executor.department ? `<br><small>${executor.department}</small>` : ''}
        </div>
    `).join('');

    suggestionsContainer.innerHTML = suggestionsHTML;
    suggestionsContainer.style.display = 'block';

    // Добавляем обработчики клика на подсказки
    suggestionsContainer.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', function() {
            const executorId = this.getAttribute('data-executor-id');
            const executorName = this.querySelector('strong').textContent;

            // Заполняем поле ввода
            input.value = executorName;
            // Сохраняем ID в data-атрибут
            input.setAttribute('data-executor-id', executorId);

            hideSuggestions(suggestionsContainer);
        });
    });
}

// Функция скрытия подсказок
function hideSuggestions(suggestionsContainer) {
    suggestionsContainer.style.display = 'none';
}

// Функция показа/скрытия загрузки
function showLoading(show) {
    // Реализуйте отображение индикатора загрузки по необходимости
    console.log('Loading:', show);
}

// Инициализация после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    const registrationNumber = getRegistrationNumberFromUrl();
    document.getElementById('registrationNumber').textContent = registrationNumber;
    const executorInput = document.querySelector('.request-executor-input');
    const suggestionsContainer = document.querySelector('.suggestions-container');

    if (!executorInput || !suggestionsContainer) return;

    // Обработчик ввода текста
    let searchTimeout;
    executorInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        searchTimeout = setTimeout(() => {
            searchExecutors(query, suggestionsContainer, this);
        }, 300); // Задержка 300мс
    });

    // Обработчик фокуса
    executorInput.addEventListener('focus', function() {
        const query = this.value.trim();
        if (query.length >= 2) {
            searchExecutors(query, suggestionsContainer, this);
        }
    });

    // Обработчик клика вне поля
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.executor-input-wrapper')) {
            hideSuggestions(suggestionsContainer);
        }
    });

    // Обработчик клавиш (для навигации стрелками)
    executorInput.addEventListener('keydown', function(event) {
        const suggestions = suggestionsContainer.querySelectorAll('.suggestion-item');
        const activeSuggestion = suggestionsContainer.querySelector('.suggestion-item.active');

        if (event.key === 'ArrowDown') {
            event.preventDefault();
            navigateSuggestions(1, suggestions, activeSuggestion);
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            navigateSuggestions(-1, suggestions, activeSuggestion);
        } else if (event.key === 'Enter' && activeSuggestion) {
            event.preventDefault();
            activeSuggestion.click();
        } else if (event.key === 'Escape') {
            hideSuggestions(suggestionsContainer);
        }
    });

    document.getElementById('requestForm').addEventListener('submit', async function(e) {
        e.preventDefault();

        const executorInput = document.querySelector('.request-executor-input');
        const executorId = executorInput.getAttribute('data-executor-id');
        const executorName = executorInput.value;
        const executorComment = document.getElementById('executorComment').value;

        // Валидация
        if (!executorId) {
            showNotification('Пожалуйста, выберите исполнителя из списка', 'error');
            executorInput.focus();
            return;
        }

        if (!registrationNumber) {
            showNotification('Не найден номер заявки', 'error');
            return;
        }

        const submitButton = document.getElementById('submitEdit');
        const originalText = submitButton.innerHTML;

        // Блокируем кнопку на время отправки
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Назначается...';

        try {
            const registrationNumber = getRegistrationNumberFromUrl();
            await submitExecutorAssignment(registrationNumber, executorId, executorComment);

            showNotification('Исполнитель успешно назначен', 'success');

            window.location.href = `/request/${registrationNumber}`;

        } catch (error) {
            console.error('Ошибка:', error);
            showNotification(error.message || 'Ошибка при назначении исполнителя', 'error');

            // Разблокируем кнопку при ошибке
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
        }
    });
});

// Функция навигации по подсказкам стрелками
function navigateSuggestions(direction, suggestions, activeSuggestion) {
    if (suggestions.length === 0) return;

    let nextIndex = 0;

    if (activeSuggestion) {
        const currentIndex = Array.from(suggestions).indexOf(activeSuggestion);
        nextIndex = currentIndex + direction;

        if (nextIndex < 0) nextIndex = suggestions.length - 1;
        if (nextIndex >= suggestions.length) nextIndex = 0;

        activeSuggestion.classList.remove('active');
    }

    suggestions[nextIndex].classList.add('active');
    suggestions[nextIndex].scrollIntoView({ block: 'nearest' });
}
