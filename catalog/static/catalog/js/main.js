document.addEventListener('DOMContentLoaded', function() {
    console.log('Genrefy загружен!');

    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-5px)';
            card.style.boxShadow = '5px 5px 10px rgba(0, 0, 0, 0.1)';
        })

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
            card.style.boxShadow = '';
        })
    })

    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    })

    function formatNumber(num) {
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num;
    }

    document.querySelectorAll('[data-count]').forEach(el => {
        const count = parseInt(el.getAttribute('data-count'));
        if (!isNaN(count)) {
            el.textContent = formatNumber(count);
        }
    })
})