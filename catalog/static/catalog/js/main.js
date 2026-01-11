(function() {
    'use strict';

    class GenrefyApp {
        constructor() {
            this.debug = true;
            this.lastfmRed = '#db221b';
            this.init();
        }

        init() {
            this.log('Genrefy инициализирован');
            this.setupEventListeners();
            this.enhanceCards();
            this.highlightActiveNav();
            this.formatHighNumbers();
            this.checkMobileView();
        }

        log(message, data = null) {
            if (this.debug) {
                console.log(`[Genrefy] ${message}`, data || '');
            }
        }

        setupEventListeners() {
            document.addEventListener('click', (e) => {
                if (e.target.matches('.card, .card *')) {
                    this.trackCardClick(e.target.closest('.card'));
                }

                if (e.target.matches('.btn')) {
                    this.trackButtonClick(e.target);
                }
            });

            window.addEventListener('resize', () => {
                this.handleResize();
                this.log('Размер окна изменен', {
                    width: window.innerWidth,
                    height: window.innerHeight
                });
            });

            window.addEventListener('beforeunload', () => {
                this.saveState();
            });
        }

        enhanceCards() {
            const cards = document.querySelectorAll('.card');

            cards.forEach((card, index) => {
                card.dataset.cardId = index;

                card.addEventListener('mouseenter', () => {
                    card.style.transition = 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)';
                    card.style.transform = 'translateY(-5px) scale(1.02)';
                    card.style.boxShadow = '0 10px 20px rgba(0, 0, 0, 0.1)';

                    this.addHoverIndicator(card);
                });

                card.addEventListener('mouseleave', () => {
                    card.style.transform = 'translateY(0) scale(1)';
                    card.style.boxShadow = '';
                    this.removeHoverIndicator(card);
                });

                card.addEventListener('click', (e) => {
                    if (!e.target.closest('a')) {
                        return;
                    }

                    this.trackCardClick(card);
                });
            });
        }

        addHoverIndicator(card) {
            const indicator = document.createElement('div');
            indicator.className = 'hover-indicator';
            indicator.style.cssText = `
                position: absolute;
                top: 10px;
                right: 10px;
                width: 8px;
                height: 8px;
                background: ${this.lastfmRed};
                border-radius: 50%;
                opacity: 0.7;
            `;
            card.style.position = 'relative';
            card.appendChild(indicator);
        }

        removeHoverIndicator(card) {
            const indicator = card.querySelector('.hover-indicator');
            if (indicator) {
                indicator.remove();
            }
        }

        toggleCardFavorite(card) {
            card.classList.toggle('favorite');
            const isFavorite = card.classList.contains('favorite');

            if (isFavorite) {
                card.style.borderLeft = `4px solid ${this.lastfmRed}`;
                this.showToast('Добавлено в избранное');
            } else {
                card.style.borderLeft = '';
                this.showToast('Удалено из избранного');
            }

            this.log('Избранное изменено', {
                cardId: card.dataset.cardId,
                isFavorite: isFavorite
            });
        }

        highlightActiveNav() {
            const currentPath = window.location.pathname;
            const navLinks = document.querySelectorAll('.nav-link');

            navLinks.forEach(link => {
                const href = link.getAttribute('href');
                if (href === currentPath ||
                    (href !== '/' && currentPath.startsWith(href))) {
                    link.classList.add('active');

                    if (!link.querySelector('.nav-indicator')) {
                        const indicator = document.createElement('span');
                        indicator.className = 'nav-indicator';
                        indicator.style.cssText = `
                            position: absolute;
                            bottom: -2px;
                            left: 0;
                            right: 0;
                            height: 2px;
                            background: ${this.lastfmRed};
                            border-radius: 2px;
                        `;
                        link.style.position = 'relative';
                        link.appendChild(indicator);
                    }
                }
            });
        }

        formatHighNumbers() {
            document.querySelectorAll('[data-format-number]').forEach(el => {
                const num = parseInt(el.textContent.replace(/\D/g, ''));
                if (!isNaN(num)) {
                    el.innerHTML = `<span title="${num.toLocaleString()}">${this.formatNumber(num)}</span>`;
                }
            });
        }

        formatNumber(num) {
            if (num >= 1000000) {
                return (num / 1000000).toFixed(1) + '<small>M</small>';
            }
            if (num >= 1000) {
                return (num / 1000).toFixed(1) + '<small>K</small>';
            }
            return num.toLocaleString();
        }

        handleResize() {
            this.checkMobileView();
        }

        checkMobileView() {
            const isMobile = window.innerWidth < 768;
            document.body.classList.toggle('mobile-view', isMobile);

            if (isMobile) {
                this.optimizeForMobile();
            }
        }

        optimizeForMobile() {
            document.querySelectorAll('.card').forEach(card => {
                card.style.transition = 'none';
            });
        }

        trackCardClick(card) {
            this.log('Клик по карточке', {
                id: card.dataset.cardId,
                title: card.querySelector('.card-title')?.textContent || 'Без названия'
            });
        }

        trackButtonClick(button) {
            this.log('Клик по кнопке', {
                text: button.textContent.trim(),
                type: button.classList.contains('btn-primary') ? 'primary' : 'secondary'
            });
        }

        showToast(message) {
            const toast = document.createElement('div');
            toast.className = 'genrefy-toast';
            toast.textContent = message;
            toast.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: ${this.lastfmRed};
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 1000;
                animation: slideIn 0.3s ease;
            `;

            document.body.appendChild(toast);

            setTimeout(() => {
                toast.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }, 3000);

            this.addToastStyles();
        }

        addToastStyles() {
            if (!document.querySelector('#toast-styles')) {
                const style = document.createElement('style');
                style.id = 'toast-styles';
                style.textContent = `
                    @keyframes slideIn {
                        from { transform: translateX(100%); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                    @keyframes slideOut {
                        from { transform: translateX(0); opacity: 1; }
                        to { transform: translateX(100%); opacity: 0; }
                    }
                    .genrefy-toast {
                        font-family: system-ui, -apple-system, sans-serif;
                        font-size: 14px;
                    }
                `;
                document.head.appendChild(style);
            }
        }

        saveState() {
            const favorites = [];
            document.querySelectorAll('.card.favorite').forEach(card => {
                favorites.push(card.dataset.cardId);
            });

            if (favorites.length > 0) {
                localStorage.setItem('genrefy_favorites', JSON.stringify(favorites));
                this.log('Сохранено состояние', { favorites });
            }
        }

        loadState() {
            const saved = localStorage.getItem('genrefy_favorites');
            if (saved) {
                try {
                    const favorites = JSON.parse(saved);
                    favorites.forEach(id => {
                        const card = document.querySelector(`[data-card-id="${id}"]`);
                        if (card) {
                            card.classList.add('favorite');
                            card.style.borderLeft = `4px solid ${this.lastfmRed}`;
                        }
                    });
                    this.log('Загружено состояние', { favorites });
                } catch (e) {
                    this.log('Ошибка загрузки состояния', e);
                }
            }
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        try {
            window.Genrefy = new GenrefyApp();
            window.Genrefy.loadState();
        } catch (error) {
            console.error('Ошибка инициализации Genrefy:', error);
        }
    });

})();