document.addEventListener('DOMContentLoaded', () => {

  // Мобильное меню
  const burgerBtn = document.getElementById('burgerBtn');
  const siteNav = document.getElementById('siteNav');

  if (burgerBtn && siteNav) {
    // клик
    burgerBtn.addEventListener('click', () => {
      const isOpen = siteNav.classList.toggle('open');
      burgerBtn.classList.toggle('active', isOpen);
      burgerBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    // Закрытие
    document.addEventListener('click', (e) => {
      if (!siteNav.contains(e.target) && !burgerBtn.contains(e.target) && siteNav.classList.contains('open')) {
        siteNav.classList.remove('open');
        burgerBtn.classList.remove('active');
        burgerBtn.setAttribute('aria-expanded', 'false');
      }
    });

    // Закрытие
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && siteNav.classList.contains('open')) {
        siteNav.classList.remove('open');
        burgerBtn.classList.remove('active');
        burgerBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // Модальные окна
  window.openModal = function (id) {
    const modal = document.getElementById(id);
    if (modal) {
      modal.classList.add('open');
      document.body.style.overflow = 'hidden'; 
    }
  };

  window.closeModal = function (id) {
    const modal = document.getElementById(id);
    if (modal) {
      modal.classList.remove('open');
      document.body.style.overflow = ''; 
    }
  };

  // Закрытие при клике на фон
  document.querySelectorAll('.modal-backdrop').forEach((modal) => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('open');
        document.body.style.overflow = '';
      }
    });
  });

  // Закрытие Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-backdrop.open').forEach((m) => {
        m.classList.remove('open');
      });
      document.body.style.overflow = '';
    }
  });

  // Маска для ввода номера телефона
  const phoneInputs = document.querySelectorAll('input[type="tel"], input[name="phone"]');
  phoneInputs.forEach((input) => {
    input.addEventListener('input', (e) => {
      let val = e.target.value.replace(/\D/g, '');
      if (!val) {
        e.target.value = '';
        return;
      }
      if (val[0] === '9') val = '7' + val;
      if (val[0] === '8') val = '7' + val.substring(1);
      if (val[0] !== '7') val = '7' + val;

      let formatted = '+7';
      if (val.length > 1) {
        formatted += ' (' + val.substring(1, 4);
      }
      if (val.length >= 5) {
        formatted += ') ' + val.substring(4, 7);
      }
      if (val.length >= 8) {
        formatted += '-' + val.substring(7, 9);
      }
      if (val.length >= 10) {
        formatted += '-' + val.substring(9, 11);
      }
      e.target.value = formatted;
    });
  });

  // поиск и фильтрация направлений
  const searchInput = document.querySelector('.search-input');
  const stylesGrid = document.getElementById('stylesGrid');
  const emptyBlock = document.getElementById('liveSearchResultsEmpty');
  const diffTabs = document.querySelectorAll('.diff-tabs-group .diff-tab');

  if (searchInput && stylesGrid) {
    let currentDiff = '';

    // Фильтрация карточек
    function filterStyles() {
      const query = searchInput.value.trim().toLowerCase();
      const cards = stylesGrid.querySelectorAll('.two-tone-card');
      let visibleCount = 0;

      cards.forEach((card) => {
        const name = card.dataset.name || '';
        const desc = card.dataset.desc || '';
        const teachers = card.dataset.teachers || '';
        const diff = card.dataset.diff || '';

        const matchesQuery = !query || name.includes(query) || desc.includes(query) || teachers.includes(query);
        const matchesDiff = !currentDiff || diff === currentDiff;

        if (matchesQuery && matchesDiff) {
          card.style.display = '';
          visibleCount++;
        } else {
          card.style.display = 'none';
        }
      });

      if (emptyBlock) {
        emptyBlock.style.display = visibleCount === 0 ? 'block' : 'none';
      }
    }

    searchInput.addEventListener('input', filterStyles);

    // Переключение уровня сложности
    diffTabs.forEach((tab) => {
      tab.addEventListener('click', (e) => {
        e.preventDefault();
        diffTabs.forEach((t) => t.classList.remove('active'));
        tab.classList.add('active');

        const href = tab.getAttribute('href');
        const match = href.match(/difficulty=([^&]+)/);
        currentDiff = match ? match[1] : '';

        filterStyles();
      });
    });

    // Сброс фильтров
    const resetBtn = document.getElementById('resetLiveFilterBtn');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        searchInput.value = '';
        currentDiff = '';
        diffTabs.forEach((t, i) => {
          if (i === 0) t.classList.add('active');
          else t.classList.remove('active');
        });
        filterStyles();
      });
    }
  }
});
