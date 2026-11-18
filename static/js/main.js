document.addEventListener('DOMContentLoaded', () => {
  const burgerBtn = document.getElementById('burgerBtn');
  const siteNav = document.getElementById('siteNav');

  if (burgerBtn && siteNav) {
    burgerBtn.addEventListener('click', () => {
      const isOpen = siteNav.classList.toggle('open');
      burgerBtn.classList.toggle('active', isOpen);
      burgerBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    document.addEventListener('click', (e) => {
      if (!siteNav.contains(e.target) && !burgerBtn.contains(e.target) && siteNav.classList.contains('open')) {
        siteNav.classList.remove('open');
        burgerBtn.classList.remove('active');
        burgerBtn.setAttribute('aria-expanded', 'false');
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && siteNav.classList.contains('open')) {
        siteNav.classList.remove('open');
        burgerBtn.classList.remove('active');
        burgerBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }

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

  document.querySelectorAll('.modal-backdrop').forEach((modal) => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('open');
        document.body.style.overflow = '';
      }
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-backdrop.open').forEach((m) => {
        m.classList.remove('open');
      });
      document.body.style.overflow = '';
    }
  });

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

  const bookingForm = document.getElementById('bookingForm');
  if (bookingForm) {
    const nameInput = bookingForm.querySelector('input[name="full_name"]');
    const phoneInput = bookingForm.querySelector('input[name="phone"]');
    const agreeInput = bookingForm.querySelector('input[name="agree_rules"]');

    function setFieldError(field, errorMsg) {
      const formGroup = field.closest('.form-group');
      if (!formGroup) return;
      formGroup.classList.add('has-error');
      let msgElem = formGroup.querySelector('.field-error-msg');
      if (!msgElem) {
        msgElem = document.createElement('div');
        msgElem.className = 'field-error-msg';
        msgElem.setAttribute('role', 'alert');
        formGroup.appendChild(msgElem);
      }
      msgElem.textContent = errorMsg;
    }

    function clearFieldError(field) {
      const formGroup = field.closest('.form-group');
      if (!formGroup) return;
      formGroup.classList.remove('has-error');
      const msgElem = formGroup.querySelector('.field-error-msg');
      if (msgElem) {
        msgElem.remove();
      }
    }

    function validateName() {
      if (!nameInput) return true;
      const val = nameInput.value.trim();
      if (!val) {
        setFieldError(nameInput, 'Поле обязательно для заполнения.');
        return false;
      }
      if (val.length < 3) {
        setFieldError(nameInput, 'Имя должно содержать не менее 3 символов.');
        return false;
      }
      if (val.split(/\s+/).length < 2) {
        setFieldError(nameInput, 'Укажите имя и фамилию через пробел.');
        return false;
      }
      clearFieldError(nameInput);
      return true;
    }

    function validatePhone() {
      if (!phoneInput) return true;
      const digits = phoneInput.value.replace(/\D/g, '');
      if (!digits) {
        setFieldError(phoneInput, 'Укажите номер телефона для связи.');
        return false;
      }
      if (digits.length !== 11) {
        setFieldError(phoneInput, 'Номер телефона должен состоять из 11 цифр (+7 XXX XXX-XX-XX).');
        return false;
      }
      clearFieldError(phoneInput);
      return true;
    }

    function validateAgree() {
      if (!agreeInput) return true;
      if (!agreeInput.checked) {
        setFieldError(agreeInput, 'Необходимо согласие с правилом отмены за 2 часа.');
        return false;
      }
      clearFieldError(agreeInput);
      return true;
    }

    if (nameInput) {
      nameInput.addEventListener('blur', validateName);
      nameInput.addEventListener('input', () => {
        if (nameInput.closest('.form-group.has-error')) validateName();
      });
    }

    if (phoneInput) {
      phoneInput.addEventListener('blur', validatePhone);
      phoneInput.addEventListener('input', () => {
        if (phoneInput.closest('.form-group.has-error')) validatePhone();
      });
    }

    if (agreeInput) {
      agreeInput.addEventListener('change', validateAgree);
    }

    bookingForm.addEventListener('submit', (e) => {
      const isNameValid = validateName();
      const isPhoneValid = validatePhone();
      const isAgreeValid = validateAgree();

      if (!isNameValid || !isPhoneValid || !isAgreeValid) {
        e.preventDefault();
        const firstError = bookingForm.querySelector('.form-group.has-error input');
        if (firstError) {
          firstError.focus();
        }
      }
    });
  }

  const searchInput = document.querySelector('.search-input');
  const stylesGrid = document.getElementById('stylesGrid');
  const emptyBlock = document.getElementById('liveSearchResultsEmpty');
  const diffTabs = document.querySelectorAll('.diff-tabs-group .diff-tab');

  if (searchInput && stylesGrid) {
    let currentDiff = '';

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
