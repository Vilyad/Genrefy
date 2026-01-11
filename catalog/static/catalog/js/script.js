function handleCardClick(url) {
    window.location.href = url;
}

function handleFavoriteClick(event, itemId, itemType = 'genre') {
    event.stopPropagation();
    event.preventDefault();

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
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showFavoriteNotification(data.action);

            updateFavoriteUI(itemId, data.is_favorite, itemType);
        } else {
            console.error('Error:', data.message);
            showNotification('Ошибка: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Ошибка сети', 'error');
    });
}

function showFavoriteNotification(action) {
    const messages = {
        'added': 'Добавлено в избранное',
        'removed': 'Удалено из избранного'
    };

    if (window.Genrefy && window.Genrefy.showToast) {
        window.Genrefy.showToast(messages[action]);
    } else {
        alert(messages[action]);
    }
}

function showNotification(message, type = 'info') {
    if (window.Genrefy && window.Genrefy.showToast) {
        window.Genrefy.showToast(message);
    } else {
        alert(message);
    }
}

function updateFavoriteUI(itemId, isFavorite, itemType = 'genre') {
    const selector = `[data-item-id="${itemId}"][data-item-type="${itemType}"]`;
    const elements = document.querySelectorAll(selector);

    elements.forEach(element => {
        if (element.classList.contains('favorite-icon')) {
            element.textContent = isFavorite ? '♥' : '♡';
            element.classList.toggle('active', isFavorite);
            element.title = isFavorite ? 'Удалить из избранного' : 'Добавить в избранное';

            element.style.transform = 'scale(1.3)';
            setTimeout(() => {
                element.style.transform = 'scale(1)';
            }, 300);
        }
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.favorite-icon').forEach(icon => {
        icon.addEventListener('click', function(e) {
            const itemId = this.getAttribute('data-item-id');
            const itemType = this.getAttribute('data-item-type') || 'genre';
            handleFavoriteClick(e, itemId, itemType);
        });
    });
});

function initGenreSearch() {
    const searchForm = document.querySelector('form[action*="genre_list"]');
    const searchInput = searchForm?.querySelector('input[name="search"]');

    if (!searchInput) return;

    let debounceTimer;

    searchInput.addEventListener('input', function(e) {
        clearTimeout(debounceTimer);

        debounceTimer = setTimeout(() => {
            const searchValue = e.target.value.trim();

            if (searchValue.length >= 2 || searchValue.length === 0) {
                const url = new URL(window.location);
                if (searchValue) {
                    url.searchParams.set('search', searchValue);
                } else {
                    url.searchParams.delete('search');
                }

                fetch(url, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newContent = doc.querySelector('.row').innerHTML;

                    document.querySelector('.row').innerHTML = newContent;

                    const countElement = document.querySelector('.text-muted strong');
                    if (countElement) {
                        const newCount = doc.querySelector('.text-muted strong')?.textContent || '0';
                        countElement.textContent = newCount;
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        }, 500);
    });
}

document.addEventListener('DOMContentLoaded', initGenreSearch);