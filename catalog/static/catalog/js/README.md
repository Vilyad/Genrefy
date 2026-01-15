# JavaScript для Genrefy

## Структура JavaScript файлов

Проект использует несколько JavaScript файлов для разных целей:

### 1. **main.js** - Основное приложение
- **Назначение:** Ядро клиентской части приложения
- **Функциональность:**
  - Анимация карточек с эффектами наведения
  - Управление избранным через localStorage
  - Toast-уведомления с кастомными стилями
  - Адаптивность под мобильные устройства
  - Автоматическое форматирование больших чисел (1K, 1M)
  - Логирование действий пользователя для аналитики
  - Подсветка активной навигации

### 2. **script.js** - Интерактивные элементы
- **Назначение:** Обработка пользовательских действий
- **Функциональность:**
  - Работа с избранным через Django API (`/toggle_favorite/`)
  - AJAX-поиск по жанрам с debounce
  - Обновление UI без перезагрузки страницы
  - Обработка CSRF токенов для POST-запросов
  - Интеграция с `main.js` для уведомлений

---

## Основные возможности

### Адаптивный интерфейс
```javascript
// Автоматическое определение мобильного вида
window.Genrefy.checkMobileView();

// Оптимизация анимаций для мобильных устройств
if (isMobile) {
    card.style.transition = 'none';
}
```

### Система избранного
#### Локальное хранение (main.js):
```javascript
// Сохранение в localStorage
localStorage.setItem('genrefy_favorites', JSON.stringify(favorites));

// Загрузка при старте
window.Genrefy.loadState();
```

#### Серверное хранение (script.js):
```javascript
// Отправка на сервер
fetch('/toggle_favorite/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({
        item_id: itemId,
        item_type: itemType
    })
});
```

### AJAX-поиск
```javascript
// Поиск с debounce (500ms)
let debounceTimer;
searchInput.addEventListener('input', function(e) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        // AJAX запрос и обновление DOM
    }, 500);
});
```

### Уведомления
```javascript
// Toast-уведомления через main.js
window.Genrefy.showToast('Добавлено в избранное');

// Или через script.js
showNotification('Ошибка сети', 'error');
```

### Анимации и эффекты
```javascript
// Анимация карточек при наведении
card.style.transform = 'translateY(-5px) scale(1.02)';
card.style.boxShadow = '0 10px 20px rgba(0, 0, 0, 0.1)';

// Индикатор Last.fm (красная точка)
indicator.style.background = '#db221b'; // Last.fm red
```

---

## API и интеграции

### Взаимодействие с Django
- **CSRF защита:** Автоматическое получение токенов
- **JSON API:** Общение с `/toggle_favorite/` endpoint
- **AJAX поиск:** Частичное обновление страницы

### Интеграция между файлами
```javascript
// script.js использует main.js для уведомлений
if (window.Genrefy && window.Genrefy.showToast) {
    window.Genrefy.showToast(message);
}

// main.js управляет UI, script.js - логикой
```

---

## Аналитика и логирование

### Отслеживание действий
```javascript
// Логирование кликов по карточкам
trackCardClick(card) {
    this.log('Клик по карточке', {
        id: card.dataset.cardId,
        title: card.querySelector('.card-title')?.textContent
    });
}

// Логирование кликов по кнопкам
trackButtonClick(button) {
    this.log('Клик по кнопке', {
        text: button.textContent.trim(),
        type: button.classList.contains('btn-primary') ? 'primary' : 'secondary'
    });
}
```

### Производительность
- **Debounce для поиска:** 500ms для оптимизации запросов
- **Адаптивные анимации:** Отключаются на мобильных
- **Ленивая загрузка:** AJAX обновление только нужных частей

---

## Использование

### Доступ к функциональности
```javascript
// Все возможности через глобальный объект
window.Genrefy.showToast('Привет!');
window.Genrefy.formatHighNumbers();
window.Genrefy.saveState();

// Или напрямую через функции
showFavoriteNotification('added');
updateFavoriteUI('123', true, 'genre');
initGenreSearch();
```

### Кастомизация
```javascript
// Настройка цвета (Last.fm red по умолчанию)
window.Genrefy.lastfmRed = '#db221b';

// Включение/выключение отладки
window.Genrefy.debug = false;
```

---

## Поддержка мобильных устройств

### Автоматическое определение
```javascript
checkMobileView() {
    const isMobile = window.innerWidth < 768;
    document.body.classList.toggle('mobile-view', isMobile);
}
```

### Оптимизации для мобильных
- Упрощенные анимации
- Крупные элементы управления
- Адаптивные сетки карточек
- Touch-friendly интерфейс

---

## Безопасность

### CSRF защита
```javascript
function getCookie(name) {
    // Автоматическое получение CSRF токена
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }
    return null;
}
```

### Безопасное хранение
- Ключи API только в переменных окружения
- CSRF токены для всех POST-запросов
- Валидация данных на клиенте и сервере

---

## Быстрый старт

### HTML разметка для избранного
```html
<button class="favorite-icon" 
        data-item-id="123" 
        data-item-type="genre"
        onclick="handleFavoriteClick(event, '123', 'genre')">
    ♡
</button>
```

### Инициализация
```html
<script src="{% static 'js/main.js' %}"></script>
<script src="{% static 'js/script.js' %}"></script>
<script>
    // Автоматическая инициализация при загрузке DOM
    document.addEventListener('DOMContentLoaded', function() {
        // main.js инициализируется автоматически
        // script.js функции доступны сразу
        
        // Дополнительная инициализация при необходимости
        if (window.location.pathname.includes('genre')) {
            initGenreSearch();
        }
    });
</script>
```

---

## Отладка

### Включение логов
```javascript
// В консоли браузера
window.Genrefy.debug = true;

// Или в коде
class GenrefyApp {
    constructor() {
        this.debug = true; // Включить логи
    }
}
```

### Проверка состояния
```javascript
// Проверить сохраненные избранные
console.log(JSON.parse(localStorage.getItem('genrefy_favorites')));

// Проверить инициализацию
console.log(window.Genrefy);
```

---

## Примечания

1. **main.js** - это ядро приложения, должно подключаться первым
2. **script.js** зависит от main.js для уведомлений
3. Все AJAX запросы требуют CSRF токен
4. Локальное избранное (localStorage) не синхронизируется с серверным
5. При отключенном JavaScript работает fallback на стандартные формы