/**
 * 1MILLION DANCE STUDIO — ОСНОВНАЯ КЛИЕНТСКАЯ ЛОГИКА
 */

document.addEventListener('DOMContentLoaded', () => {
  const burgerBtn = document.getElementById('burgerBtn');
  const siteNav = document.getElementById('siteNav');

  if (burgerBtn && siteNav) {
    burgerBtn.addEventListener('click', () => {
      const isOpen = siteNav.classList.toggle('open');
      burgerBtn.classList.toggle('active', isOpen);
      burgerBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    // Закрытие меню при клике вне его области
    document.addEventListener('click', (e) => {
      if (!siteNav.contains(e.target) && !burgerBtn.contains(e.target) && siteNav.classList.contains('open')) {
        siteNav.classList.remove('open');
        burgerBtn.classList.remove('active');
        burgerBtn.setAttribute('aria-expanded', 'false');
      }
    });

    // Закрытие при нажатии Esc
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && siteNav.classList.contains('open')) {
        siteNav.classList.remove('open');
        burgerBtn.classList.remove('active');
        burgerBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }
});
