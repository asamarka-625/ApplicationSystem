const API_BASE_URL = 'http://localhost:8000/api/v1/request/create';

async function loadCreateInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/info`);
        const data = await response.json();
        const info = data.departament;
        const request_type = data.request_type;

        const select1 = document.getElementById('');
        info.forEach(site => {
            const option = document.createElement('option');
            option.value = site.code;
            option.textContent = site.name;
            select1.appendChild(option);
        });

        const select2 = document.getElementById('requestType');
        request_type.forEach(site => {
            const option = document.createElement('option');
            option.value = site;
            option.textContent = site;
            select2.appendChild(option);
        });

    } catch (error) {
        console.error('Ошибка загрузки судебных участков:', error);
        showNotification('Ошибка загрузки справочников', 'error');
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
    
    const formData = new FormData(form);
    
    // Остальной код без изменений
    const requestData = {
        itemId: formData.get('itemId'),
        description: formData.get('description'),
        request_type_id: formData.get('requestTypeId'),
        departament_Id: formData.get('departamentId'),
        is_emergency: formData.get('requestType') === 'Аварийная'
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
	const searchInput = document.getElementById('requestTitle');
	const suggestionsContainer = document.getElementById('suggestions');

	// Накладываем событие на ввод с debounce
	let searchTimeout;
	searchInput.addEventListener('input', function(event) {
		const searchTerm = event.target.value.trim();

		// Очищаем предыдущий таймер
		clearTimeout(searchTimeout);

		// Если строка не пустая, отправляем запрос через 300ms
		if (searchTerm.length > 2) {
			searchTimeout = setTimeout(() => {
				searchItems(searchTerm);
			}, 300);
		} else {
			hideSuggestions();
		}
	});
	
	// Функция для скрытия подсказок
	function hideSuggestions() {
		suggestionsContainer.style.display = 'none';
	}

	// Функция для отображения подсказок
	function displaySuggestions(items) {
		if (!items || items.length === 0) {
			hideSuggestions();
			return;
		}

		const suggestionsHTML = items.map(name => `
			<div class="suggestion-item" data-value="${name}">
				${name}
			</div>
		`).join('');

		suggestionsContainer.innerHTML = suggestionsHTML;
		suggestionsContainer.style.display = 'block';
	}

	// Обработчик клика по подсказке
	suggestionsContainer.addEventListener('click', function(event) {
		if (event.target.classList.contains('suggestion-item')) {
			const value = event.target.getAttribute('data-value');
			searchInput.value = value;
			hideSuggestions();
		}
	});

	// Скрываем подсказки при клике вне input
	document.addEventListener('click', function(event) {
		if (!searchInput.contains(event.target) && !suggestionsContainer.contains(event.target)) {
			hideSuggestions();
		}
	});

	// Дополнительные обработчики для клавиатуры
	searchInput.addEventListener('keydown', function(event) {
		if (event.key === 'Escape') {
			hideSuggestions();
		}
	});
	
	// Функция для отправки запроса
	async function searchItems(query) {
		try {
			showLoading(true);
			const response = await fetch(`${API_BASE_URL}/item/?search=${encodeURIComponent(query)}`);

			if (!response.ok) {
				throw new Error('Ошибка сети');
			}

			const results = await response.json();
			displaySuggestions(results);

		} catch (error) {
			console.error('Ошибка поиска:', error);
			hideSuggestions();
			
		} finally {
			showLoading(false);
		}
	}
	
	document.getElementById('sumbit_create').addEventListener('click', handleRequestSubmit);
});