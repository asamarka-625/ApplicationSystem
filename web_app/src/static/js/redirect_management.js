const API_URL = '/api/v1/request/create';
const API_BASE_URL = '/api/v1/request';

function getRegistrationNumberFromUrl() {
    const url = window.location.href;
    const parts = url.split('/');
    const registrationNumber = parts[parts.length - 3];
    return registrationNumber;
}

async function submitManagementAssignment(registrationNumber, managementId, managementComment) {
    try {
        const response = await fetch(`${API_BASE_URL}/redirect/management/${registrationNumber}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_role_id: managementId,
                description: managementComment || ''
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;

    } catch (error) {
        console.error('Ошибка назначения сотрудника:', error);
        throw error;
    }
}

// Функция загрузки списка сотрудников управления
async function loadManagements() {
    try {
        const response = await fetch(`${API_URL}/managements`);
        if (!response.ok) {
            throw new Error('Ошибка сети');
        }
        const results = await response.json();
        displayManagementList(results);
    } catch (error) {
        console.error('Ошибка загрузки сотрудников:', error);
        showNotification('Ошибка загрузки списка сотрудников', 'error');
    }
}

// Функция отображения списка сотрудников
function displayManagementList(managements) {
    const suggestionsContainer = document.querySelector('.suggestions-container');

    if (!managements || managements.length === 0) {
        suggestionsContainer.innerHTML = '<div class="suggestion-item">Сотрудники не найдены</div>';
        suggestionsContainer.style.display = 'block';
        return;
    }

    const suggestionsHTML = managements.map(management => `
        <div class="suggestion-item" data-management-id="${management.id}">
            <strong>${management.full_name}</strong>
            ${management.division ? `<small>${management.division}</small>` : ''}
        </div>
    `).join('');

    suggestionsContainer.innerHTML = suggestionsHTML;
    suggestionsContainer.style.display = 'block';

    // Добавляем обработчики клика на элементы списка
    suggestionsContainer.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', function() {
            const managementId = this.getAttribute('data-management-id');
            const managementName = this.querySelector('strong').textContent;

            // Заполняем поле ввода
            const managementInput = document.querySelector('.request-management-input');
            managementInput.value = managementName;
            managementInput.setAttribute('data-management-id', managementId);

            hideSuggestions(suggestionsContainer);
        });
    });
}

// Функция скрытия списка
function hideSuggestions(suggestionsContainer) {
    suggestionsContainer.style.display = 'none';
}

// Инициализация после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    const registrationNumber = getRegistrationNumberFromUrl();
    document.getElementById('registrationNumber').textContent = registrationNumber;

    const managementInput = document.querySelector('.request-management-input');
    const suggestionsContainer = document.querySelector('.suggestions-container');

    if (!managementInput || !suggestionsContainer) return;

    // Загружаем список сотрудников при фокусе на поле
    managementInput.addEventListener('focus', function() {
        loadManagements();
    });

    // Обработчик клика вне поля
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.management-input-wrapper')) {
            hideSuggestions(suggestionsContainer);
        }
    });

    // Обработчик клавиш (для навигации стрелками)
    managementInput.addEventListener('keydown', function(event) {
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

        const managementInput = document.querySelector('.request-management-input');
        const managementId = managementInput.getAttribute('data-management-id');
        const managementComment = document.getElementById('managementComment').value;

        // Валидация
        if (!managementId) {
            showNotification('Пожалуйста, выберите сотрудника из списка', 'error');
            managementInput.focus();
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
            await submitManagementAssignment(registrationNumber, managementId, managementComment);

            showNotification('Сотрудник успешно назначен', 'success');
            window.location.href = `/request/${registrationNumber}`;

        } catch (error) {
            console.error('Ошибка:', error);
            showNotification(error.message || 'Ошибка при назначении сотрудника', 'error');
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
        }
    });
});

// Функция навигации по списку стрелками
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