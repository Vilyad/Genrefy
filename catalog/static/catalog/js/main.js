(function() {
    'use strict';

    class GenrefyApp {
        constructor() {
            this.init();
        }

        init() {
            console.log('Genrefy инициализирован');
            this.setupEventListeners();
            this.enhanceCards();
            this.highlightActiveNav();
            this.formatHighNumbers();
        }
        
        setupEventListeners() {
            document.addEventListener('click', (e) => {
                if (e.target.matches('.card, .card *')) {
                    console.log('Клик по карточке:', e.target);
                }
            });

            window.addEventListener('resize', this.handleResize.bind(this));
        }

        enhanceCards() {
            const cards = document.querySelectorAll('.card');

            cards.forEach(card => {
                card.addEventListener('mouseenter', () => {
                    card.style.transition = 'all 0.3 ease';
                    card.style.transform = 'translateY(-5px) scale(1.02)';
                    card.style.boxShadow = '5px 5px 10px rgba(0, 0, 0, 0.1)';
                });

                card.addEventListener('mouseleave', () => {
                    card.style.transform = 'translateY(0) scale(1)';
                    card.style.boxShadow = '';
                });

                card.addEventListener('click', () => {
                    card.classList.toggle('active');
                });
            });
        }

        highlightActiveNav() {
            const currentPath = window.location.pathname;
            const navLinks = document.querySelectorAll('.nav-link');

            navLinks.forEach(link => {
                const href = link.getAttribute('href')
                if (href === currentPath ||
                    (href !== '/' && currentPath.startsWith(href))) {
                    link.classList.add('active');
                    link.style.fontWeight = '600';
                }
            });
        }

        formatHighNumbers() {
            document.querySelectorAll('[data-format-number]').forEach(el => {
                const num = parseInt(el.textContent);
                if (!isNaN(num)) {
                    el.textContent = this.formatNumber(num);
                }
            });
        }
        

        formatNumber(num) {
            if (num >= 1000000) {
                return (num / 1000000).toFixed(1) + 'M'
            }
            if (num >= 1000) {
                return (num / 1000).toFixed(1) + 'K';
            }
            return num.toString();
        }

        handleResize() {
            const isMobile = window.innerWidth < 768;
            document.body.classList.toggle('mobile-view', isMobile);
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        window.Genrefy = new GenrefyApp();
    });

})();