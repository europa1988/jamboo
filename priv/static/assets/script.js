// Управление мобильным меню
const hamburger = document.getElementById('hamburger');
const menuOverlay = document.getElementById('menuOverlay');
const mobileMenu = document.getElementById('mobileMenu');

function toggleMobileMenu() {
    menuOverlay.classList.toggle('hidden');
    mobileMenu.classList.toggle('active');
    document.body.classList.toggle('overflow-hidden');
}

if (hamburger) {
    hamburger.addEventListener('click', toggleMobileMenu);
}
if (menuOverlay) {
    menuOverlay.addEventListener('click', toggleMobileMenu);
}
if (mobileMenu) {
    mobileMenu.querySelectorAll('a, button, .category-item').forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth < 768) toggleMobileMenu();
        });
    });
}

// Анимация категорий
document.querySelectorAll('.category-item').forEach(item => {
    item.addEventListener('mouseenter', () => item.style.transform = 'translateX(5px)');
    item.addEventListener('mouseleave', () => item.style.transform = 'translateX(0)');
});

// Скрытие шапки при скролле
let lastScrollTop = 0;
const header = document.getElementById('mainHeader');
if (header) {
    const headerHeight = header.offsetHeight;
    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        if (scrollTop > lastScrollTop && scrollTop > headerHeight) {
            header.classList.remove('header-visible');
            header.classList.add('header-hidden');
        } else {
            header.classList.remove('header-hidden');
            header.classList.add('header-visible');
        }
        lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
    });
}

// Аккордеоны
document.querySelectorAll('.accordion-header').forEach(header => {
    header.addEventListener('click', () => {
        const content = header.nextElementSibling;
        const icon = header.querySelector('.material-icons');
        content.classList.toggle('open');
        icon.textContent = content.classList.contains('open') ? 'expand_less' : 'expand_more';
    });
});

// Выпадающее меню пользователя
const userMenuBtn = document.getElementById('userMenuBtn');
const userDropdown = document.getElementById('userDropdown');

if (userMenuBtn && userDropdown) {
    userMenuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        userDropdown.classList.toggle('show');
    });
    
    // Закрытие при клике вне меню
    document.addEventListener('click', (e) => {
        if (!userMenuBtn.contains(e.target) && !userDropdown.contains(e.target)) {
            userDropdown.classList.remove('show');
        }
    });
}

// Инициализация после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    // --- КАРУСЕЛЬ (без двойных стрелок) ---
    const swiperContainer = document.querySelector('.news-swiper');
    if (swiperContainer && typeof Swiper !== 'undefined') {
        const swiper = new Swiper('.news-swiper', {
            loop: false,
            slidesPerView: 1,
            spaceBetween: 15,
            autoplay: { delay: 5000, disableOnInteraction: false },
            // НЕ указываем navigation — используем свои кнопки
            breakpoints: {
                640: { slidesPerView: 2, spaceBetween: 15 },
                1024: { slidesPerView: 3, spaceBetween: 20 }
            }
        });
        // Привязываем свои кнопки
        const prevBtn = document.querySelector('.news-swiper .swiper-button-prev');
        const nextBtn = document.querySelector('.news-swiper .swiper-button-next');
        if (prevBtn) prevBtn.addEventListener('click', () => swiper.slidePrev());
        if (nextBtn) nextBtn.addEventListener('click', () => swiper.slideNext());
        // Пауза при наведении
        swiperContainer.addEventListener('mouseenter', () => swiper.autoplay.stop());
        swiperContainer.addEventListener('mouseleave', () => swiper.autoplay.start());
    }

    // --- ГОЛОСОВАНИЕ ---
    function updateVoteCounter(element, change, type = null) {
        let countText = element.textContent;
        let count = parseFloat(countText);
        if (countText.includes('k')) count = parseFloat(countText) * 1000;
        count += change;
        let displayCount;
        if (count >= 10000) displayCount = (count / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
        else if (count >= 1000) displayCount = (count / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
        else displayCount = Math.round(count).toString();
        element.textContent = displayCount;
        if (type) {
            element.classList.remove('positive', 'negative');
            if (type === 'up') element.classList.add('positive');
            else if (type === 'down') element.classList.add('negative');
        }
        element.classList.remove('changed');
        void element.offsetWidth;
        element.classList.add('changed');
    }

    document.querySelectorAll('.vote-btn:not(.comment-actions .vote-btn)').forEach(btn => {
        btn.addEventListener('click', function() {
            const container = this.closest('.voting-container');
            const countElement = container.querySelector('.vote-count');
            const isUp = this.classList.contains('up');
            const isActive = this.classList.contains('active');
            container.querySelectorAll('.vote-btn').forEach(b => b.classList.remove('active'));
            if (isActive) {
                updateVoteCounter(countElement, isUp ? -1 : 1, isUp ? 'up' : 'down');
            } else {
                this.classList.add('active');
                updateVoteCounter(countElement, isUp ? 1 : -1, isUp ? 'up' : 'down');
            }
        });
    });

    // --- ТЕМНАЯ ТЕМА ---
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    if (themeToggle && themeIcon) {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark' || (!savedTheme && prefersDark.matches)) {
            document.documentElement.classList.add('dark');
            themeIcon.textContent = 'light_mode';
        } else {
            document.documentElement.classList.remove('dark');
            themeIcon.textContent = 'dark_mode';
        }
        themeToggle.addEventListener('click', () => {
            const isDark = document.documentElement.classList.toggle('dark');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            themeIcon.textContent = isDark ? 'light_mode' : 'dark_mode';
        });
    }

    // --- КОММЕНТАРИИ (если есть на странице) ---
    document.querySelectorAll('.toggle-reply').forEach(btn => {
        btn.addEventListener('click', function() {
            const replyForm = this.closest('.comment-content').querySelector('.reply-form');
            if (replyForm) replyForm.classList.toggle('active');
        });
    });
    document.querySelectorAll('.cancel-reply').forEach(btn => {
        btn.addEventListener('click', function() {
            const form = this.closest('.reply-form');
            if (form) form.classList.remove('active');
        });
    });
    document.querySelectorAll('.comment-actions button').forEach(btn => {
        btn.addEventListener('click', function() {
            const isUp = this.classList.contains('up');
            const container = this.closest('.comment-actions');
            const countEl = container.querySelector('.comment-vote-count');
            const isActive = this.classList.contains('active');
            container.querySelectorAll('button').forEach(b => b.classList.remove('active'));
            if (isActive) {
                updateVoteCounter(countEl, isUp ? -1 : 1);
            } else {
                this.classList.add('active');
                updateVoteCounter(countEl, isUp ? 1 : -1);
            }
        });
    });
    const commentForm = document.querySelector('.comment-form');
    if (commentForm) {
        commentForm.addEventListener('submit', e => {
            e.preventDefault();
            const ta = commentForm.querySelector('textarea');
            if (ta && ta.value.trim()) {
                alert('Комментарий отправлен!');
                ta.value = '';
            }
        });
    }

    // --- ВКЛАДКИ ПРОФИЛЯ ---
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.tab-btn').forEach(b => {
                b.classList.remove('active', 'border-jamboo-orange', 'text-gray-800');
                b.classList.add('text-gray-600');
            });
            this.classList.add('active', 'border-jamboo-orange', 'text-gray-800');
            this.classList.remove('text-gray-600');
            const tabIndex = Array.from(this.parentElement.children).indexOf(this);
            document.querySelectorAll('.tab-content').forEach((content, idx) => {
                content.classList.toggle('active', idx === tabIndex);
            });
        });
    });
});